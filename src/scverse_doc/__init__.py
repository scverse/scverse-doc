"""The scverse Sphinx theme and shared documentation configuration.

A package’s `conf.py` needs few lines:

.. code:: python

   extensions = ["scverse_doc"]

   html_theme_options = {"repo": "scverse/pertpy"}

This extension sets up the subextensions,
each of which also works on its own:

:mod:`scverse_doc.config`
    The extension stack and the shared defaults.
:mod:`scverse_doc.registry`
    The package registry, usable as an :func:`~scverse_doc.registry.intersphinx` mapping.
:mod:`scverse_doc.theme`
    The theme, its chrome, and the per-package accent.

Anything set in `conf.py` wins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.util.typing import ExtensionMetadata

from . import config, registry, theme
from .config import _is_set_by_user

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["config", "registry", "theme", "setup"]


def _default_theme(app: Sphinx, config: Config) -> None:
    """Select the theme, since the umbrella extension means it too, unless `conf.py` picked another."""
    if not _is_set_by_user(config, "html_theme"):
        config.html_theme = "scverse"


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up the registry and the subextensions."""
    for extension in set(__all__) - {"setup"}:
        app.setup_extension(f"scverse_doc.{extension}")
    app.connect("config-inited", _default_theme)
    return ExtensionMetadata(parallel_read_safe=True)
