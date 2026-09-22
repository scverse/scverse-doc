"""The scverse theme: brand chrome, the per-package accent, and the ecosystem dropdown.

:mod:`scverse_doc` selects this theme; on its own, set ``html_theme = "scverse"``.
Declare the package with the :ref:`theme options <theme-options>`;
`pydata-sphinx-theme`’s own options work as well.
This theme sets up :mod:`scverse_doc.source`, which adds the repository links.
The accent colour and the “scverse packages” dropdown come from the
:mod:`registry <scverse_doc.registry>`, without any configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from sphinx.util.typing import ExtensionMetadata

from .._color import derive_readable
from ..registry import DEFAULT_ACCENT, _build_cache, packages

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["setup"]

_THEME_PATH = Path(__file__).parent / "scverse"

#: `pydata-sphinx-theme`’s page backgrounds, which the derived accents must be readable on.
_LIGHT_BACKGROUND = "#ffffff"
_DARK_BACKGROUND = "#14181e"

_ACCENT_CSS = """\
:root {{
  --scverse-color-accent-decorative: {accent};
  --scverse-color-accent-text: light-dark({light}, {dark});
}}
"""

#: ``fa-scverse`` is not a real Font Awesome glyph – the theme stylesheet masks the synced logo into it.
_ICON_LINKS = (
    {"name": "Discourse", "url": "https://discourse.scverse.org/", "icon": "fa-brands fa-discourse"},
    {"name": "scverse", "url": "https://scverse.org/", "icon": "fa-scverse"},
)


def _package_name(config: Config) -> str:
    return str(config.html_theme_options.get("package") or config.project)


def _accent(config: Config) -> str:
    if accent := config.html_theme_options.get("accent"):
        return str(accent)
    if (pkg := packages.get(_package_name(config))) is not None:
        return pkg.accent
    return DEFAULT_ACCENT


def _add_chrome(config: Config) -> None:
    """Add the brand icon links and the colour mode, alongside whatever :mod:`scverse_doc.source` set."""
    options = config.html_theme_options
    # Appended, so this works whichever order `scverse_doc.source`’s hook runs in.
    options["icon_links"] = [*options.get("icon_links", []), *_ICON_LINKS]
    config.html_context = {"default_mode": "auto", **config.html_context}


def _configure(app: Sphinx) -> None:
    """Expand the declared theme options and generate the accent stylesheet.

    Only for `html_theme = "scverse"`: the options written here are `pydata-sphinx-theme`’s.

    On ``builder-inited``, not ``config-inited``: selecting the theme without listing this
    extension loads it from the ``sphinx.html_themes`` entry point, which Sphinx only does
    when the builder creates the theme – long after ``config-inited``.
    `pydata-sphinx-theme` reads these options from the same event, but connects later.
    """
    config = app.config
    if config.html_theme != "scverse":
        return

    _add_chrome(config)

    accent = _accent(config)
    static_dir = _build_cache(app) / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "scverse-accent.css").write_text(
        _ACCENT_CSS.format(
            accent=accent,
            light=derive_readable(accent, _LIGHT_BACKGROUND),
            dark=derive_readable(accent, _DARK_BACKGROUND),
        )
    )
    config.html_static_path = [*config.html_static_path, str(static_dir)]
    app.add_css_file("scverse-accent.css")


def _add_ecosystem_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: object,
) -> None:
    """Expose the registry to the navbar dropdown template."""
    if app.config.html_theme != "scverse":
        return
    current = _package_name(app.config).lower()
    groups: dict[str, list[dict[str, Any]]] = {"core": [], "ecosystem": []}
    for pkg in packages.values():
        groups[pkg.kind].append({"name": pkg.name, "docs": pkg.docs, "current": pkg.name.lower() == current})
    context["scverse_ecosystem"] = groups


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the theme, its templates, and the build hooks."""
    app.add_html_theme("scverse", str(_THEME_PATH))
    app.config.templates_path = [*app.config.templates_path, str(_THEME_PATH / "components")]
    app.setup_extension("scverse_doc.source")

    app.connect("builder-inited", _configure)
    app.connect("html-page-context", _add_ecosystem_context)

    return ExtensionMetadata(parallel_read_safe=True)
