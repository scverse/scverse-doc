# SPDX-License-Identifier: MPL-2.0
"""Sphinx docs configuration."""

import sys
from pathlib import Path

from scverse_doc.config import DEFAULTS
from scverse_doc.registry import intersphinx

# `examples.py` holds the objects the API pages demo the subextensions with.
sys.path.insert(0, str(Path(__file__).parent))

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
# included by the `release-notes` example
exclude_patterns = [*DEFAULTS.exclude_patterns, "api/release-notes-example"]
xref_overrides = {"concurrent.futures.thread.ThreadPoolExecutor": "concurrent.futures.ThreadPoolExecutor"}

# This package documents Sphinx internals, which no other scverse package needs.
intersphinx_mapping = intersphinx() | {"sphinx": ("https://www.sphinx-doc.org/en/master/", None)}
