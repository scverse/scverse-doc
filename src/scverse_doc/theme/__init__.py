"""The theme: brand chrome, the per-package accent, and the ecosystem dropdown.

Registers ``html_theme = "scverse"`` and translates the options a package declares
(:confval:`package`, :confval:`repo`, :confval:`accent`) into what `pydata-sphinx-theme` expects.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sphinx.util.typing import ExtensionMetadata

from .._color import derive_readable
from ..registry import DEFAULT_ACCENT, build_cache, packages

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

THEME_PATH = Path(__file__).parent / "scverse"

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


def _branch(options: dict[str, Any]) -> str:
    """The ref edit links point at: the option, else what Read the Docs is building, else ``main``."""
    if branch := options.get("branch"):
        return str(branch)
    # On pull request builds the identifier is the PR number, not a ref.
    if os.environ.get("READTHEDOCS_VERSION_TYPE") != "external" and (
        ref := os.environ.get("READTHEDOCS_GIT_IDENTIFIER")
    ):
        return ref
    return "main"


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
            "github_version": _branch(options),
            "doc_path": options.get("doc_path", "docs/"),
            "default_mode": "auto",
            **config.html_context,
        }
    options["icon_links"] = [*icon_links, *_ICON_LINKS]


def configure(app: Sphinx, config: Config) -> None:
    """Expand the declared theme options and generate the accent stylesheet.

    Only for `html_theme = "scverse"`: the options written here are `pydata-sphinx-theme`’s.
    """
    if config.html_theme != "scverse":
        return

    _expand_repo(config)

    accent = _accent(config)
    static_dir = build_cache(app) / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "scverse-accent.css").write_text(
        _ACCENT_CSS.format(
            accent=accent,
            light=derive_readable(accent, LIGHT_BACKGROUND),
            dark=derive_readable(accent, DARK_BACKGROUND),
        )
    )
    config.html_static_path = [*config.html_static_path, str(static_dir)]
    app.add_css_file("scverse-accent.css")


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


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the theme, its templates, and the build hooks."""
    app.add_html_theme("scverse", str(THEME_PATH))
    app.config.templates_path = [*app.config.templates_path, str(THEME_PATH / "components")]

    app.connect("config-inited", configure)
    app.connect("html-page-context", add_ecosystem_context)

    return ExtensionMetadata(parallel_read_safe=True)
