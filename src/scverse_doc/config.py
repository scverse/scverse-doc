# SPDX-License-Identifier: MPL-2.0
"""The extension stack and the shared defaults.

Sets up the extensions in :data:`EXTENSIONS`, so `conf.py` lists only ``scverse_doc``,
and fills in :data:`DEFAULTS`. Anything set in `conf.py` always wins.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING, Final

from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["DEFAULTS", "EXTENSIONS", "Defaults", "MYST_ENABLE_EXTENSIONS", "setup"]

#: Extensions set up alongside this one,
#: so packages list only ``scverse_doc``.
EXTENSIONS: Final = (
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxext.opengraph",
)

#: The MyST syntax extensions, i.e. the ``myst_enable_extensions`` entry of :data:`~scverse_doc.config.DEFAULTS`.
MYST_ENABLE_EXTENSIONS: Final = (
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "html_admonition",
)


@dataclass(frozen=True)
class Defaults:
    """Sphinx config values applied unless `conf.py` sets them."""

    autosummary_generate: bool = True
    autodoc_member_order: str = "groupwise"
    napoleon_google_docstring: bool = False
    napoleon_numpy_docstring: bool = True
    napoleon_include_init_with_doc: bool = False
    napoleon_use_param: bool = True
    napoleon_use_rtype: bool = True
    default_role: str = "literal"
    myst_enable_extensions: list[str] = field(default_factory=lambda: list(MYST_ENABLE_EXTENSIONS))
    myst_heading_anchors: int = 6
    source_suffix: dict[str, str] = field(
        default_factory=lambda: {".rst": "restructuredtext", ".md": "myst-nb", ".ipynb": "myst-nb"}
    )
    # Off: tutorials needing a GPU or a large download must not gate a docs build.
    nb_execution_mode: str = "off"
    nb_output_stderr: str = "remove"
    nb_merge_streams: bool = True
    # One unreachable host must not stall the build.
    intersphinx_timeout: int = 10
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
    )
    nitpicky: bool = True


#: Sphinx config values applied unless `conf.py` sets them.
DEFAULTS: Final = Defaults()


def _is_set_by_user(config: Config, name: str) -> bool:
    """Report whether `conf.py` or a ``-D`` override set `name`."""
    return name in config._raw_config or name in config._overrides


def _apply_defaults(config: Config) -> None:
    """Fill in the values `conf.py` did not set."""
    # A fresh instance, so builds don't share (and mutate) the same lists and dicts.
    defaults = Defaults()
    for f in fields(defaults):
        if _is_set_by_user(config, f.name):
            continue
        setattr(config, f.name, getattr(defaults, f.name))


def _configure(app: Sphinx, config: Config) -> None:
    _apply_defaults(config)
    if not _is_set_by_user(config, "html_title"):
        config.html_title = config.project


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up the extension stack and apply the defaults."""
    for extension in EXTENSIONS:
        app.setup_extension(extension)
    app.connect("config-inited", _configure)
    return ExtensionMetadata(parallel_read_safe=True)
