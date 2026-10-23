# SPDX-License-Identifier: MPL-2.0
"""Sphinx docs configuration."""

from sphinx.application import Sphinx

project = "scverse-doc"
extensions = [
    "scverse_doc",
    "sphinxcontrib.bibtex",
    "sphinx.ext.linkcode",
    "sphinx_toolbox.rest_example",
]
html_logo = "_static/scverse.svg"
html_theme_options = {"announcement": ""}
source_repository = "https://github.com/scverse/scverse-doc"

bibtex_bibfiles = ["references.bib"]

# This package documents Sphinx internals, which no other scverse package needs.
from scverse_doc.registry import intersphinx  # noqa: E402

intersphinx_mapping = intersphinx() | {"sphinx": ("https://www.sphinx-doc.org/en/master/", None)}


def setup(app: Sphinx) -> None:  # noqa: D103
    # `sphinx_toolbox.rest_example` needs this, but only gets it from parsing an .rst file, and ours are all MyST
    app.config.docutils_tab_width = 8
