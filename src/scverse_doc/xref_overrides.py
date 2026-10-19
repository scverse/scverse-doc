# SPDX-License-Identifier: MPL-2.0
"""Cross-references to objects documented under another name or role.

A type annotation links to ``{module}.{qualname}`` of the object,
which is often a private path like ``pandas.core.frame.DataFrame``,
while the object is documented as :class:`pandas.DataFrame`.
The config value ``xref_overrides`` maps one to the other:

.. code:: python

   xref_overrides = {
       "pandas.core.frame.DataFrame": "pandas.DataFrame",  # fix qualname
       "numpy.int64": ("py:data", "numpy.int64"),  # fix role
   }

Keys can also be ``(role, name)`` tuples, to only override references with that role.
:data:`DEFAULT_OVERRIDES` are always included.
Entries from `conf.py` that no reference needed are reported after a full build.
``qualname_overrides``, the name in scanpydoc, still works, but is deprecated.

So that annotations from ``if TYPE_CHECKING:`` blocks also link to their full name,
the imports in these blocks are executed before autodoc evaluates a signature.
"""

from __future__ import annotations

import ast
import inspect
import sys
from dataclasses import dataclass, field
from functools import cache
from typing import TYPE_CHECKING

from sphinx.util import logging
from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import ModuleType
    from typing import Any

    from docutils import nodes
    from sphinx.addnodes import pending_xref
    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment

    type _Key = tuple[str | None, str]

__all__ = ["DEFAULT_OVERRIDES", "setup"]

_logger = logging.getLogger(__name__)

#: Overrides included in addition to the ``xref_overrides`` from `conf.py`.
DEFAULT_OVERRIDES: dict[str, str] = {
    "anndata._core.anndata.AnnData": "anndata.AnnData",
    "matplotlib.axes._axes.Axes": "matplotlib.axes.Axes",
    "pandas.core.frame.DataFrame": "pandas.DataFrame",
    "pandas.core.indexes.base.Index": "pandas.Index",
}


def _normalize(mapping: Mapping[Any, str | _Key]) -> dict[_Key, _Key]:
    """Make keys and values ``(role, name)`` tuples, with role :data:`None` for any role."""
    return {
        (k if isinstance(k, tuple) else (None, k)): (v if isinstance(v, tuple) else (None, v))
        for k, v in mapping.items()
    }


@cache  # keyed on the module object, so a re-imported module is handled again
def _exec_guarded_imports(module: ModuleType) -> None:
    """Execute the ``if TYPE_CHECKING:`` blocks of a module in its namespace, once."""
    try:
        tree = ast.parse(inspect.getsource(module))
    except (OSError, TypeError, SyntaxError):
        return
    for node in tree.body:
        if not (isinstance(node, ast.If) and ast.unparse(node.test) in {"TYPE_CHECKING", "typing.TYPE_CHECKING"}):
            continue
        for stmt in node.body:  # one by one, so one failing import doesn’t lose the others
            try:
                exec(
                    compile(ast.Module([stmt], type_ignores=[]), module.__file__ or module.__name__, "exec"),
                    module.__dict__,
                )
            except Exception:  # noqa: BLE001
                _logger.debug(f"Failed to execute guarded import {ast.unparse(stmt)!r} in {module.__name__}")


def _resolve_guarded_imports(app: Sphinx, obj: Any, bound_method: bool) -> None:
    if isinstance(module_name := getattr(obj, "__module__", None), str) and module_name in sys.modules:
        _exec_guarded_imports(sys.modules[module_name])


@dataclass
class _Overrides:
    """The overrides of one build, and which of them were used."""

    overrides: dict[_Key, _Key] = field(default_factory=dict)
    used: set[_Key] = field(default_factory=set)
    resolved_docs: set[str] = field(default_factory=set)

    def init(self, app: Sphinx, config: Config) -> None:
        if config.qualname_overrides:
            _logger.warning("`qualname_overrides` is deprecated, use `xref_overrides`")
            config.xref_overrides = config.qualname_overrides | config.xref_overrides
        self.overrides = _normalize(DEFAULT_OVERRIDES) | _normalize(config.xref_overrides)

    def resolve(
        self, app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: nodes.TextElement
    ) -> nodes.reference | None:
        """Rewrite the reference, then resolve it locally or leave it to intersphinx."""
        role = f"{node['refdomain']}:{node['reftype']}"
        for key in [(role, node["reftarget"]), (None, node["reftarget"])]:
            if (ref := self.overrides.get(key)) is not None:
                break
        else:
            return None
        self.used.add(key)
        new_role, node["reftarget"] = ref
        if new_role is not None:
            node["refdomain"], node["reftype"] = new_role.split(":", 1)
        domain = env.get_domain(node["refdomain"])
        return domain.resolve_xref(env, node["refdoc"], app.builder, node["reftype"], node["reftarget"], node, contnode)

    def mark_resolved(self, app: Sphinx, doctree: nodes.document, docname: str) -> None:
        self.resolved_docs.add(docname)

    def report_unused(self, app: Sphinx, exception: Exception | None) -> None:
        # Incremental builds only resolve some documents, so only full builds know what’s unused.
        if exception is not None or not app.env.found_docs <= self.resolved_docs:
            return
        for key in _normalize(app.config.xref_overrides).keys() - self.used:
            _logger.info(f"note: unused xref_overrides entry {key[1] if key[0] is None else key}")


def setup(app: Sphinx) -> ExtensionMetadata:
    """Add the ``xref_overrides`` config value and resolve references with it."""
    app.setup_extension("sphinx.ext.autodoc")
    app.setup_extension("sphinx.ext.intersphinx")
    app.add_config_value("xref_overrides", {}, "env", types=frozenset({dict}))
    app.add_config_value("qualname_overrides", {}, "env", types=frozenset({dict}))  # deprecated alias
    overrides = _Overrides()
    app.connect("config-inited", overrides.init)
    app.connect("autodoc-before-process-signature", _resolve_guarded_imports)
    # Before intersphinx (500), so it resolves the rewritten reference if the domain can’t.
    app.connect("missing-reference", overrides.resolve, priority=499)
    app.connect("doctree-resolved", overrides.mark_resolved)
    app.connect("build-finished", overrides.report_unused)
    return ExtensionMetadata(parallel_read_safe=True)
