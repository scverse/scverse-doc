"""Shared defaults applied to every scverse documentation build.

Everything here is a *default*:
a value set in `conf.py` always wins.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sphinx.config import Config

__all__ = ["DEFAULTS", "EXTENSIONS", "MYST_ENABLE_EXTENSIONS", "apply_defaults"]

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

MYST_ENABLE_EXTENSIONS = (
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "html_admonition",
)

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
    # Off by default:
    # tutorials needing a GPU or a large download must not gate a docs build.
    "nb_execution_mode": "off",
    "nb_output_stderr": "remove",
    "nb_merge_streams": True,
    # 17 inventories resolve by default,
    # so one unreachable host must not stall the build.
    "intersphinx_timeout": 10,
    "exclude_patterns": ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"],
    "nitpicky": True,
}


def _is_set_by_user(config: Config, name: str) -> bool:
    """Report whether `conf.py` or a ``-D`` override set `name`."""
    return name in config._raw_config or name in config._overrides


def apply_defaults(config: Config) -> list[str]:
    """Fill in the values `conf.py` did not set, and return the names that were applied.

    Parameters
    ----------
    config
        The Sphinx configuration, mutated in place.

    Returns
    -------
    list[str]
        The names of the defaults that were applied.
    """
    applied = []
    for name, value in DEFAULTS.items():
        if _is_set_by_user(config, name):
            continue
        setattr(config, name, value)
        applied.append(name)
    return applied
