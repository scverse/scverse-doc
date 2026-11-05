# SPDX-License-Identifier: MPL-2.0
"""A release notes directive.

Given a directory of version files matching :data:`FULL_VERSION_RE`,
render them grouped by minor version (where ``.`` is the directory they are in):

.. code:: rst

   .. release-notes:: .

Each file is parsed by the parser for its suffix (see `source_suffix`), or else like the page.
A file in another format than the page is parsed on its own, so its headings start at the top level
(e.g. ``#`` in Markdown).
With e.g. the files :file:`1.2.0.md`, :file:`1.2.1.md`, and :file:`1.3.0.rst`,
this renders like the following:

.. code:: rst

   .. _v1.3:

   Version 1.3
   ===========

   .. include:: 1.3.0.rst


   .. _v1.2:

   Version 1.2
   ===========

   .. include:: 1.2.1.md
      :parser: myst_parser.sphinx_
   .. include:: 1.2.0.md
      :parser: myst_parser.sphinx_
"""

from __future__ import annotations

import itertools
import re
from copy import copy
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from docutils import nodes
from docutils.utils import new_document
from packaging.version import Version
from sphinx.errors import FiletypeNotFoundError
from sphinx.util import get_filetype
from sphinx.util.docutils import SphinxDirective
from sphinx.util.parsing import nested_parse_to_nodes
from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from myst_parser.mdit_to_docutils.base import DocutilsRenderer
    from sphinx.application import Sphinx

__all__ = ["FULL_VERSION_RE", "ReleaseNotes", "setup"]

FULL_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:.*)?$")
"""Regex matching a full version number including patch part, maybe with more after."""


@dataclass
class _Backend:
    dir: Path
    instance: SphinxDirective
    #: The format the directive is in, which :meth:`render_native` parses.
    filetype: ClassVar[str] = "restructuredtext"

    def run(self) -> Sequence[nodes.Node]:
        versions = sorted(
            ((Version(f.stem), f) for f in self.dir.iterdir() if FULL_VERSION_RE.match(f.stem)),
            reverse=True,  # descending
        )
        version_groups = itertools.groupby(versions, key=lambda vf: (vf[0].major, vf[0].minor))
        return [
            node
            for (major, minor), versions in version_groups
            for node in self.render_version_group(major, minor, versions)
        ]

    def render_version_group(
        self, major: int, minor: int, versions: Iterable[tuple[Version, Path]] = ()
    ) -> tuple[nodes.target, nodes.section]:
        target = nodes.target(ids=[f"v{major}-{minor}"], names=[f"v{major}.{minor}"])
        section = nodes.section(
            "", nodes.title("", f"Version {major}.{minor}"), ids=[], names=[f"version {major}.{minor}"]
        )

        self.instance.state.document.note_implicit_target(section)
        self.instance.state.document.note_explicit_target(target)

        for _, p in versions:
            section += self.render_include(p)
        return target, section

    def render_include(self, path: Path) -> Sequence[nodes.Node]:
        """Parse `path` with the parser for its suffix, falling back to the page’s."""
        env = self.instance.env
        try:
            filetype = get_filetype(env.config.source_suffix, path)
        except FiletypeNotFoundError:  # e.g. `.txt`
            filetype = self.filetype
        if filetype == self.filetype:
            return self.render_native(path)
        # Like docutils’ ``include`` with ``:parser:``: parse into a document sharing the page’s targets
        parser = env._registry.create_source_parser(filetype, config=env.config, env=env)
        page = self.instance.state.document
        document = new_document(str(path), copy(page.settings))
        document.ids, document.nameids, document.nametypes = page.ids, page.nameids, page.nametypes
        document.include_log = page.include_log
        parser.parse(path.read_text(), document)
        page.parse_messages.extend(document.parse_messages)
        return document.children

    def render_native(self, path: Path) -> Sequence[nodes.Node]:
        """Parse `path` as part of the page, in its heading context."""
        return nested_parse_to_nodes(
            self.instance.state, path.read_text(), source=str(path), offset=self.instance.content_offset
        )


# TODO(flying-sheep): Remove once MyST-Parser bug is fixed
# https://github.com/executablebooks/MyST-Parser/issues/967
class _BackendMyst(_Backend):
    filetype: ClassVar[str] = "markdown"

    def run(self) -> Sequence[nodes.Node]:
        super().run()
        return []

    def render_version_group(
        self, major: int, minor: int, versions: Iterable[tuple[Version, Path]] = ()
    ) -> tuple[nodes.target, nodes.section]:
        target, section = super().render_version_group(major, minor)
        # append target and section to parent
        self._myst_renderer.current_node.append(target)
        self._myst_renderer.update_section_level_state(section, 2)
        # append children to section
        for _, p in versions:
            with self._myst_renderer.current_node_context(section):
                section += self.render_include(p)
        return target, section  # ignored, just to not change the types

    def render_native(self, path: Path) -> Sequence[nodes.Node]:
        from docutils.parsers.rst.directives.misc import Include
        from myst_parser.mocking import MockIncludeDirective

        srcfile, lineno = self.instance.get_source_info()
        if srcfile is None or lineno is None:  # pragma: no cover
            msg = "Could not determine source info."
            raise self.instance.error(msg)
        parent_dir = Path(srcfile).parent

        d = MockIncludeDirective(
            renderer=self._myst_renderer,
            name=type(self).__name__,
            klass=Include,
            arguments=[str(path.relative_to(parent_dir))],
            options={},
            body=[],
            lineno=lineno,
        )
        return d.run()  # renders into the current node

    @property
    def _myst_renderer(self) -> DocutilsRenderer:
        rv: DocutilsRenderer = self.instance.state._renderer  # type: ignore[attr-defined]
        return rv


class ReleaseNotes(SphinxDirective):
    """Directive rendering release notes, grouping them by minor versions."""

    required_arguments: ClassVar = 1

    def run(self) -> Sequence[nodes.Node]:
        """Read the release notes and render them."""
        dir_ = Path(self.arguments[0])
        # resolve relative dir
        if not dir_.is_absolute():
            # nested content (e.g. in another directive) has no source, so fall back to the document
            src_file = Path(s) if (s := self.get_source_info()[0]) else self.env.doc2path(self.env.docname)
            if not src_file.is_file():
                msg = f"Cannot find relative path to: {src_file}"
                raise self.error(msg)
            dir_ = src_file.parent / self.arguments[0]
        if not dir_.is_dir():
            msg = f"Not a directory: {dir_}"
            raise self.error(msg)

        cls = _BackendMyst if hasattr(self.state, "_renderer") else _Backend
        return cls(dir_, self).run()


def setup(app: Sphinx) -> ExtensionMetadata:
    """Add the ``release-notes`` directive."""
    app.add_directive("release-notes", ReleaseNotes)
    return ExtensionMetadata(parallel_read_safe=True)
