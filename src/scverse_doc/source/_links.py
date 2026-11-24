# SPDX-License-Identifier: MPL-2.0
"""Links to the code: ``[source]`` links via :mod:`sphinx.ext.linkcode`, and edit links on autosummary stubs."""

from __future__ import annotations

import inspect
from importlib import import_module
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, cast

from sphinx.ext.autosummary import ImportExceptionGroup, import_by_name
from sphinx.ext.autosummary.generate import find_autosummary_in_files

from ._forge import Source
from ._locate import locate

if TYPE_CHECKING:
    from docutils import nodes
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

__all__ = ["configure_linkcode", "find_stubs", "linkcode_url", "point_edit_links_at_code"]


def linkcode_url(source: Source, module: str, fullname: str, srcdir: Path | None = None) -> str | None:
    """Link to a Python object’s definition, or :data:`None` if it has no findable source in this repository.

    Modules in `srcdir` (the docs’ own helpers) link into :confval:`source_directory`.
    """
    if (location := locate(module, fullname)) is None:
        return None
    file, span = location
    if srcdir is not None and file.is_relative_to(srcdir):
        return source.view(PurePosixPath(source.directory, *file.relative_to(srcdir).parts), span)
    # The documented package’s directory, or file for a single-module one.
    package = Path(inspect.getsourcefile(import_module(module.partition(".")[0])) or "")
    package = package.parent if package.name == "__init__.py" else package
    # Objects re-exported from other packages (or the stdlib) live in other repositories.
    if not file.is_relative_to(package):
        return None
    # Relative to the package, since a non-editable install puts it outside the checkout.
    return source.view(PurePosixPath(source.code, *file.relative_to(package.parent).parts), span)


def configure_linkcode(app: Sphinx) -> None:
    """Resolve `sphinx.ext.linkcode`’s links, if `conf.py` asked for it but defined no resolver."""
    config = app.config
    if "sphinx.ext.linkcode" not in app.extensions or config.linkcode_resolve is not None:
        return
    if (source := Source.from_config(config)) is None:
        return

    def linkcode_resolve(domain: str, info: dict[str, str]) -> str | None:
        if domain != "py" or not info["module"]:
            return None
        return linkcode_url(source, info["module"], info["fullname"], Path(app.srcdir))

    config.linkcode_resolve = linkcode_resolve


def find_stubs(app: Sphinx, env: BuildEnvironment, docnames: list[str]) -> None:
    """Record ``{stub docname: object name}`` for the pages ``autosummary_generate`` writes.

    Uses the same text scan as ``autosummary_generate``, so it also finds directives that are never parsed,
    e.g. in a comment with a separate hidden ``toctree``.
    Runs on every build after the stubs are written and found, so it includes stubs generated from stubs.
    """
    if not getattr(app.config, "autosummary_generate", False):
        return
    srcdir = Path(app.srcdir).resolve()
    filename_map: dict[str, str] = getattr(app.config, "autosummary_filename_map", {})
    entries = find_autosummary_in_files([env.doc2path(doc) for doc in env.found_docs])
    stubs = {
        (Path(entry.path).resolve() / filename_map.get(entry.name, entry.name)): entry.name
        for entry in entries
        if entry.path is not None
    }
    env.__dict__["scverse_autosummary_stubs"] = {
        path.relative_to(srcdir).as_posix(): name for path, name in stubs.items() if path.is_relative_to(srcdir)
    }


def _object_url(source: Source, name: str, srcdir: Path | None = None) -> str | None:
    """Link to the definition of the object with dotted `name`, or :data:`None` if it has no findable source."""
    try:
        _, obj, _, module = import_by_name(name)
    except ImportExceptionGroup:  # pragma: no cover
        return None
    # A submodule comes back as an attribute of its parent.
    module = obj.__name__ if inspect.ismodule(obj) else module
    return linkcode_url(source, module, name.removeprefix(module).lstrip("."), srcdir)


def point_edit_links_at_code(
    app: Sphinx, pagename: str, templatename: str, context: dict[str, object], doctree: nodes.document | None
) -> None:
    """Make the edit links on autosummary stubs point at the documented object’s source.

    Those pages are generated into the build’s source tree, so the themes’ links to them would 404.
    Sets the per-page values each theme reads, before the themes’ own ``html-page-context`` handlers run.
    """
    if (source := Source.from_config(app.config)) is None or not source.provider:
        return
    if (name := app.env.__dict__.get("scverse_autosummary_stubs", {}).get(pagename)) is None:
        return
    if (url := _object_url(source, name, Path(app.srcdir))) is None:
        # No source to point at: hide the links rather than have them 404.
        context["page_source_suffix"] = ""  # pydata-sphinx-theme, sphinx-book-theme, furo
        context[f"display_{source.provider.name}"] = False  # sphinx_rtd_theme
        return
    context.update(
        {
            # pydata-sphinx-theme and sphinx-book-theme; the comment passes the check for a `file_name` placeholder.
            "edit_page_url_template": f"{url}{{# file_name #}}",
            "edit_page_provider_name": source.provider.label,
            # furo
            "theme_source_edit_link": url,
            "theme_source_view_link": url,
            # sphinx_rtd_theme; copied, since it’s the environment’s own metadata
            "meta": {**cast("dict[str, object]", context.get("meta") or {}), f"{source.provider.name}_url": url},
        }
    )
