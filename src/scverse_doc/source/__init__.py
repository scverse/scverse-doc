# SPDX-License-Identifier: MPL-2.0
"""Links into the source repository: the repository icon, “edit this page”, and ``[source]``.

Declare the repository with :confval:`source_repository`.
Whatever the selected theme understands is filled in: `pydata-sphinx-theme`’s
`html_context` entries, `furo`’s and `sphinx-book-theme`’s theme options, and the icon link.

If `conf.py` lists :mod:`sphinx.ext.linkcode`, this also resolves that extension’s
``[source]`` links.

Hosts other than GitHub work as long as their URLs are laid out like GitHub’s,
GitLab’s or Bitbucket’s; :confval:`source_provider` names the layout for a self-hosted one.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.util.typing import ExtensionMetadata

from ._forge import configure_theme
from ._links import configure_linkcode, find_stubs, point_edit_links_at_code

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__all__ = ["setup"]


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the ``source_*`` config values and wire them into the theme and linkcode."""
    app.add_config_value("source_repository", "", "env", types=frozenset({str}))
    app.add_config_value("source_branch", "", "env", types=frozenset({str}))
    app.add_config_value("source_directory", "docs", "env", types=frozenset({str}))
    app.add_config_value("source_code_directory", "src", "env", types=frozenset({str}))
    app.add_config_value("source_provider", "", "env", types=frozenset({str}))

    app.connect("builder-inited", configure_linkcode)
    app.connect("builder-inited", configure_theme)
    app.connect("env-before-read-docs", find_stubs)
    # Before pydata-sphinx-theme (500) and sphinx-book-theme (501) read the context.
    app.connect("html-page-context", point_edit_links_at_code, priority=499)

    return ExtensionMetadata(parallel_read_safe=True)
