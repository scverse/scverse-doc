"""Sphinx docs configuration."""

project = "scverse-doc"
extensions = ["scverse_doc", "sphinxcontrib.bibtex", "sphinx.ext.linkcode"]
html_theme_options = {"announcement": ""}
source_repository = "https://github.com/scverse/scverse-doc"

bibtex_bibfiles = ["references.bib"]

# This package documents Sphinx internals, which no other scverse package needs.
from scverse_doc.registry import intersphinx  # noqa: E402

intersphinx_mapping = intersphinx() | {"sphinx": ("https://www.sphinx-doc.org/en/master/", None)}
