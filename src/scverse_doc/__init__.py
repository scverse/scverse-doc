"""The scverse Sphinx theme and shared documentation configuration.

A package's `conf.py` needs two lines:

.. code:: python

   extensions = ["scverse_doc"]
   html_theme = "scverse"

   html_theme_options = {"repo": "scverse/pertpy"}

The extension stack, the brand, the navigation conventions, and cross-links to every core package come from here.
Anything set in `conf.py` wins.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from . import config, registry
from ._ext import setup
from .registry import intersphinx

__all__ = ["config", "intersphinx", "registry", "setup"]

try:
    __version__ = version("scverse-doc")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"
