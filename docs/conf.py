"""Sphinx docs configuration."""

project = "scverse-doc"
extensions = ["scverse_doc", "sphinxcontrib.bibtex"]
html_theme = "scverse"
html_theme_options = {"repo": "scverse/scverse-doc", "announcement": ""}

bibtex_bibfiles = ["references.bib"]

# This package documents Sphinx internals, which no other scverse package needs.
from scverse_doc import intersphinx  # noqa: E402

intersphinx_mapping = intersphinx() | {"sphinx": ("https://www.sphinx-doc.org/en/master/", None)}

# Autodoc renders the annotation unqualified, so it cannot be resolved against Sphinx's inventory.
nitpick_ignore = [("py:class", "Config")]
