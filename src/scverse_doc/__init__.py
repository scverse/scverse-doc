"""The scverse Sphinx theme and shared documentation configuration.

A package’s `conf.py` needs few lines:

.. code:: python

   extensions = ["scverse_doc"]
   html_theme = "scverse"

   html_theme_options = {"repo": "scverse/pertpy"}

This extension wires up the `registry` and sets up the subextensions,
each of which also works on its own:

:mod:`scverse_doc.config`
    The extension stack and the shared defaults.
:mod:`scverse_doc.theme`
    The theme, its chrome, and the per-package accent.

Anything set in `conf.py` wins.
"""

from __future__ import annotations

from collections import ChainMap
from typing import TYPE_CHECKING

from sphinx.util.typing import ExtensionMetadata

from . import config, registry
from .config import _is_set_by_user
from .registry import build_cache, intersphinx

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["config", "intersphinx", "registry", "setup"]

SUBEXTENSIONS = ("scverse_doc.config", "scverse_doc.theme")


def configure_intersphinx(app: Sphinx, config: Config) -> None:
    """Default `intersphinx_mapping` to :func:`intersphinx`, and resolve what a `conf.py` built with it."""
    if not _is_set_by_user(config, "intersphinx_mapping"):
        config.intersphinx_mapping = dict(intersphinx())
    elif isinstance(config.intersphinx_mapping, ChainMap):
        config.intersphinx_mapping = dict(config.intersphinx_mapping)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up the registry and the subextensions."""
    build_cache(app)

    for extension in SUBEXTENSIONS:
        app.setup_extension(extension)
    app.connect("config-inited", configure_intersphinx)

    return ExtensionMetadata(parallel_read_safe=True)
