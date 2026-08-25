"""The Sphinx extension.

Registers the theme, pulls in the extension stack,
and fills in everything a scverse `conf.py` would otherwise repeat.
"""

from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any

from . import registry
from ._color import derive_readable
from .config import EXTENSIONS, _is_set_by_user, apply_defaults
from .registry import DEFAULT_ACCENT, intersphinx, packages

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

THEME_PATH = Path(__file__).parent / "theme" / "scverse"

#: `pydata-sphinx-theme`’s page backgrounds, which the derived accents must be readable on.
LIGHT_BACKGROUND = "#ffffff"
DARK_BACKGROUND = "#14181e"

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


def _expand_repo(config: Config) -> None:
    """Turn the single ``repo`` theme option into the GitHub chrome pydata expects."""
    options = config.html_theme_options
    icon_links = list(options.get("icon_links", []))
    if repo := str(options.get("repo", "")):
        owner, _, name = repo.partition("/")
        icon_links.insert(0, {"name": "GitHub", "url": f"https://github.com/{repo}", "icon": "fa-brands fa-github"})
        options.setdefault("use_edit_page_button", True)
        config.html_context = {
            "github_user": owner,
            "github_repo": name,
            "github_version": options.get("branch", "main"),
            "doc_path": options.get("doc_path", "docs/"),
            "default_mode": "auto",
            **config.html_context,
        }
    options["icon_links"] = [*icon_links, *_ICON_LINKS]


def configure(app: Sphinx, config: Config) -> None:
    """Apply the scverse defaults to a build that opted in via `html_theme`."""
    if config.html_theme != "scverse":
        return

    apply_defaults(config)
    _expand_repo(config)

    if not _is_set_by_user(config, "intersphinx_mapping"):
        config.intersphinx_mapping = intersphinx()
    if not _is_set_by_user(config, "html_title"):
        config.html_title = config.project

    accent = _accent(config)
    static_dir = Path(mkdtemp(prefix="scverse-doc-"))
    (static_dir / "scverse-accent.css").write_text(
        _ACCENT_CSS.format(
            accent=accent,
            light=derive_readable(accent, LIGHT_BACKGROUND),
            dark=derive_readable(accent, DARK_BACKGROUND),
        )
    )
    config.html_static_path.append(str(static_dir))
    app.add_css_file("scverse-accent.css")
    app.connect("build-finished", lambda *_: rmtree(static_dir, ignore_errors=True))


def add_ecosystem_context(
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


def setup(app: Sphinx) -> dict[str, Any]:
    """Register the theme, the extension stack, and the build hooks."""
    app.add_html_theme("scverse", str(THEME_PATH))
    app.config.templates_path.append(str(THEME_PATH / "components"))

    # Cache the upstream package listing where intersphinx caches its inventories
    # (``doctreedir/__intersphinx_cache__``), so cleaning the build directory fetches it again.
    registry.cache_dir = Path(app.doctreedir)

    for extension in EXTENSIONS:
        app.setup_extension(extension)

    app.connect("config-inited", configure)
    app.connect("html-page-context", add_ecosystem_context)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
