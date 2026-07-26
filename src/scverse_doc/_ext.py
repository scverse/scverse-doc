"""Build-time hooks.

Only things that genuinely need to run during the build live here: the accent stylesheet (which depends on the
package's colour and so cannot be a static file), the registry-driven navbar dropdown, and the guard that keeps
packages from reaching past the config layer into base-theme options.
"""

from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Any

from sphinx.util import logging

from ._color import derive_readable
from .registry import DEFAULT_ACCENT, get, packages

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config

logger = logging.getLogger(__name__)

THEME_PATH = Path(__file__).parent / "theme" / "scverse"

#: The backgrounds the derived accents must be readable on.
#: These are `pydata-sphinx-theme`'s own page backgrounds; :mod:`scverse_doc._color` targets WCAG AA against them.
LIGHT_BACKGROUND = "#ffffff"
DARK_BACKGROUND = "#14181e"

_ACCENT_CSS = """\
/* GENERATED per build from the package accent — see scverse_doc._color. */
html[data-theme="light"] {{
  --scverse-color-accent-decorative: {accent};
  --scverse-color-accent-text: {light};
}}
html[data-theme="dark"] {{
  --scverse-color-accent-decorative: {accent};
  --scverse-color-accent-text: {dark};
}}
"""


def _accent(config: Config) -> str:
    """Resolve the accent for this build, preferring an explicit override over the registry."""
    options: dict[str, Any] = config.html_theme_options
    if accent := options.get("scverse_accent"):
        return str(accent)
    if (pkg := get(str(options.get("scverse_package", "")))) is not None:
        return pkg.accent
    return DEFAULT_ACCENT


def write_accent_stylesheet(app: Sphinx, config: Config) -> None:
    """Emit the per-package accent stylesheet and register it.

    The accent cannot be a static file because the readable variants depend on the package's colour, and it cannot be
    inlined into the page because that would defeat caching.
    So it is generated into a build-local static directory that is appended to `html_static_path`.
    """
    if config.html_theme != "scverse":
        return

    accent = _accent(config)
    # Not under outdir: Sphinx warns about static paths inside the output directory, and not under the source tree
    # either, since generated files have no business being there.
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
    app.add_css_file("scverse-dark.css")
    app.connect("build-finished", lambda *_: rmtree(static_dir, ignore_errors=True))


def check_owned_options(app: Sphinx, config: Config) -> None:
    """Warn when a package configures the theme without going through the config layer.

    A package that sets base-theme options directly stops inheriting improvements to them, which is the failure mode
    this whole package exists to prevent.
    """
    if config.html_theme != "scverse":
        return
    if "scverse_package" not in config.html_theme_options:
        logger.warning(
            "html_theme_options was not produced by scverse_doc.config.theme_options(); "
            "base-theme options set by hand will not track changes to the scverse theme",
            type="scverse",
            subtype="theme_options",
        )


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
    current = str(app.config.html_theme_options.get("scverse_package", "")).lower()
    groups: dict[str, list[dict[str, Any]]] = {"core": [], "ecosystem": []}
    for pkg in packages().values():
        groups[pkg.kind].append({"name": pkg.name, "docs": pkg.docs, "current": pkg.name.lower() == current})
    context["scverse_ecosystem"] = groups


def setup(app: Sphinx) -> dict[str, Any]:
    """Register the theme and its build hooks."""
    app.add_html_theme("scverse", str(THEME_PATH))
    app.config.templates_path.append(str(THEME_PATH / "components"))

    app.connect("config-inited", write_accent_stylesheet)
    app.connect("config-inited", check_owned_options)
    app.connect("html-page-context", add_ecosystem_context)

    return {"parallel_read_safe": True, "parallel_write_safe": True}
