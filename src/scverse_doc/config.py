"""The shared `conf.py` surface.

Packages declare *intent* — which package this is, which repository it lives in — and this module translates that
into whatever the base theme currently wants.
That indirection is the point: when `pydata-sphinx-theme` renames an option, it is fixed here once instead of in
every scverse repository, which is the whole premise of shipping a theme as a dependency rather than as template
files.

For the same reason, packages are not expected to set `html_theme_options` themselves.
:func:`~scverse_doc.setup_docs` warns when they set a key this module owns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .registry import get, intersphinx

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = ["EXTENSIONS", "MYST_ENABLE_EXTENSIONS", "defaults", "intersphinx", "theme_options"]

#: The canonical extension stack.
#: ``scverse_doc`` itself is included because the theme registers itself and its build hooks as an extension.
EXTENSIONS = (
    "scverse_doc",
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxext.opengraph",
)

#: The MyST extension set every scverse package gets, so the same markup works everywhere.
MYST_ENABLE_EXTENSIONS = (
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    "html_admonition",
)

#: `html_theme_options` keys this package owns.
#: Setting these downstream defeats the single-upgrade-point promise, so :func:`~scverse_doc.setup_docs` warns.
OWNED_THEME_OPTIONS = frozenset(
    {
        "announcement",
        "footer_center",
        "footer_end",
        "footer_start",
        "logo",
        "navbar_align",
        "navbar_end",
        "navbar_persistent",
        "navbar_start",
        "pygments_dark_style",
        "pygments_light_style",
        "scverse_accent",
        "scverse_package",
        "secondary_sidebar_items",
        "show_nav_level",
        "show_toc_level",
        "use_edit_page_button",
    }
)

#: Announcement banner shared by the whole ecosystem.
#: Governance publishes one HTML fragment and every package picks it up on its next build, with no release needed.
ANNOUNCEMENT_URL = "https://scverse.org/announcement.html"


def defaults() -> dict[str, Any]:
    """Return the configuration values that are identical in every scverse package.

    These are the ~40 lines of `conf.py` boilerplate that the RFC identifies as duplicated: extensions, MyST,
    napoleon, autosummary, notebook execution, and source suffixes.

    Returns
    -------
    A mapping of Sphinx config names to values, ready to splat into a `conf.py` namespace.
    """
    return {
        "extensions": list(EXTENSIONS),
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
        "myst_url_schemes": ("http", "https", "mailto"),
        "source_suffix": {".rst": "restructuredtext", ".md": "myst-nb", ".ipynb": "myst-nb"},
        # Off by default: tutorials needing a GPU or a large download must not gate a docs build.
        "nb_execution_mode": "off",
        "nb_output_stderr": "remove",
        "nb_merge_streams": True,
        # 17 inventories resolve by default, so one unreachable host must not stall the build.
        "intersphinx_timeout": 10,
        "exclude_patterns": ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"],
        "nitpicky": True,
        "pygments_style": "default",
    }


def theme_options(
    *,
    repo: str | None = None,
    package: str | None = None,
    accent: str | None = None,
    ecosystem_dropdown: bool = True,
    extra_icon_links: Sequence[dict[str, str]] = (),
    announcement: str | None = ANNOUNCEMENT_URL,
) -> dict[str, Any]:
    """Build `html_theme_options` from scverse-level intent.

    Parameters
    ----------
    repo
        The GitHub repository as ``"owner/name"``, e.g. ``"scverse/pertpy"``.
        Drives the source link, the "edit this page" button, and the GitHub icon in the navbar.
    package
        The package's registry name.
        Supplies the accent and, in the navbar dropdown, marks the current package.
    accent
        Overrides the accent from the registry.
        Expected to be rare: the registry is the better place for a package's colour.
    ecosystem_dropdown
        Whether to show the "scverse packages" dropdown that makes the ecosystem navigable.
    extra_icon_links
        Additional pydata `icon_links` entries, appended after the standard scverse set.
    announcement
        URL of an HTML fragment shown as the announcement banner, or :data:`None` to disable it.

    Returns
    -------
    A mapping ready to assign to `html_theme_options`.
    """
    pkg = get(package) if package else None
    icon_links: list[dict[str, str]] = []
    if repo:
        icon_links.append(
            {
                "name": "GitHub",
                "url": f"https://github.com/{repo}",
                "icon": "fa-brands fa-github",
                "type": "fontawesome",
            }
        )
    icon_links += [
        {
            "name": "Discourse",
            "url": "https://discourse.scverse.org/",
            "icon": "fa-brands fa-discourse",
            "type": "fontawesome",
        },
        {
            "name": "scverse",
            "url": "https://scverse.org/",
            "icon": "fa-solid fa-house",
            "type": "fontawesome",
        },
        *extra_icon_links,
    ]

    options: dict[str, Any] = {
        "scverse_package": pkg.name if pkg else (package or ""),
        "scverse_accent": accent or (pkg.accent if pkg else ""),
        "scverse_show_ecosystem_dropdown": ecosystem_dropdown,
        "icon_links": icon_links,
        "use_edit_page_button": bool(repo),
        "navbar_align": "left",
        "navbar_start": ["navbar-logo"],
        "navbar_center": ["navbar-nav"],
        "navbar_end": ["scverse-ecosystem", "theme-switcher", "navbar-icon-links"],
        "navbar_persistent": ["search-button"],
        "secondary_sidebar_items": ["page-toc", "edit-this-page", "sourcelink"],
        "show_nav_level": 0,
        "show_toc_level": 2,
        "navigation_depth": 3,
        "collapse_navigation": False,
        "footer_start": ["scverse-footer"],
        "footer_center": [],
        "footer_end": [],
        "pygments_light_style": "tango",
        "pygments_dark_style": "monokai",
    }
    if announcement:
        options["announcement"] = announcement
    return options
