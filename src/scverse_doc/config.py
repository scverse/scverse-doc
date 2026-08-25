"""The extension stack and the shared defaults.

:data:`EXTENSIONS` are set up on top of this one, :data:`DEFAULTS` are applied to the config.
Both are *defaults*: a value set in `conf.py` always wins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["DEFAULTS", "EXTENSIONS", "MYST_ENABLE_EXTENSIONS", "setup"]

#: Extensions set up alongside this one,
#: so packages list only ``scverse_doc``.
EXTENSIONS = (
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
MYST_ENABLE_EXTENSIONS = (
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "html_admonition",
)

#: Sphinx config values applied unless `conf.py` sets them.
DEFAULTS: dict[str, Any] = {
    "autosummary_generate": True,
    "autodoc_member_order": "groupwise",
    "napoleon_google_docstring": False,
    "napoleon_numpy_docstring": True,
    "napoleon_include_init_with_doc": False,
    "napoleon_use_param": True,
    "napoleon_use_rtype": True,
    "default_role": "literal",
    "myst_enable_extensions": list(MYST_ENABLE_EXTENSIONS),
    "myst_heading_anchors": 6,
    "source_suffix": {".rst": "restructuredtext", ".md": "myst-nb", ".ipynb": "myst-nb"},
    # Off: tutorials needing a GPU or a large download must not gate a docs build.
    "nb_execution_mode": "off",
    "nb_output_stderr": "remove",
    "nb_merge_streams": True,
    # One unreachable host must not stall the build.
    "intersphinx_timeout": 10,
    "exclude_patterns": ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"],
    "nitpicky": True,
}


def _is_set_by_user(config: Config, name: str) -> bool:
    """Report whether `conf.py` or a ``-D`` override set `name`."""
    return name in config._raw_config or name in config._overrides


def _apply_defaults(config: Config) -> None:
    """Fill in the values `conf.py` did not set."""
    for name, value in DEFAULTS.items():
        if _is_set_by_user(config, name):
            continue
        setattr(config, name, value)


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
