# SPDX-License-Identifier: MPL-2.0
"""The scverse theme: brand chrome, the per-package accent, and the ecosystem dropdown.

:mod:`scverse_doc` selects this theme; on its own, set ``html_theme = "scverse"``.
Declare the package with the :ref:`theme options <theme-options>`;
`pydata-sphinx-theme`’s own options work as well.
This theme sets up :mod:`scverse_doc.source`, which adds the repository links.
The accent colour and the “scverse packages” dropdown come from the
:mod:`registry <scverse_doc.registry>`, without any configuration.
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypedDict

from docutils import nodes
from sphinx import addnodes
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.environment.adapters.toctree import _resolve_toctree
from sphinx.util.typing import ExtensionMetadata

from ..registry import DEFAULT_ACCENT, _build_cache, packages
from ._bundle import bundle, find_lightningcss

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.config import Config


class _Toctree(Protocol):
    """The ``toctree`` template function: a lambda around `StandaloneHTMLBuilder._get_local_toctree`."""

    def __call__(
        self, *, collapse: bool = ..., maxdepth: int = ..., includehidden: bool = ..., **kwargs: bool
    ) -> str: ...


class _PageContext(TypedDict, total=False):
    """The `html-page-context` template context, with the keys this theme reads or sets."""

    toctree: _Toctree


__all__ = ["setup"]

_THEME_PATH = Path(__file__).parent / "scverse"

#: `pydata-sphinx-theme`’s page backgrounds, which the derived accents must be readable on.
_LIGHT_BACKGROUND = "#ffffff"
_DARK_BACKGROUND = "#14181e"

#: OKLCH lightness bounds at which any hue and chroma meets WCAG AA on `_LIGHT_BACKGROUND` / `_DARK_BACKGROUND`;
#: ``tests/test_color.py`` checks them.
_MAX_LIGHTNESS_ON_LIGHT = 0.54
_MIN_LIGHTNESS_ON_DARK = 0.66

_ACCENT_CSS = f"""\
:root {{{{
  --scverse-color-accent-decorative: {{accent}};
  --scverse-color-accent-text: light-dark(
    oklch(from var(--scverse-color-accent-decorative) min(l, {_MAX_LIGHTNESS_ON_LIGHT}) c h),
    oklch(from var(--scverse-color-accent-decorative) max(l, {_MIN_LIGHTNESS_ON_DARK}) c h)
  );
}}}}
"""

_SECONDARY_ACCENT_CSS = f"""\
:root {{{{
  --scverse-color-secondary-accent-text: light-dark(
    oklch(from {{accent}} min(l, {_MAX_LIGHTNESS_ON_LIGHT}) c h),
    oklch(from {{accent}} max(l, {_MIN_LIGHTNESS_ON_DARK}) c h)
  );
}}}}
"""

#: scverse.org itself is linked from the scverse menu beside them.
_ICON_LINKS = ({"name": "Discourse", "url": "https://discourse.scverse.org/", "icon": "fa-brands fa-discourse"},)


def _package_name(config: Config) -> str:
    return str(config.html_theme_options.get("package") or config.project)


def _accent(config: Config) -> str:
    if accent := config.html_theme_options.get("accent"):
        return str(accent)
    if (pkg := packages.get(_package_name(config))) is not None:
        return pkg.accent
    return DEFAULT_ACCENT


def _secondary_accent(config: Config) -> str | None:
    accent: str | bool = config.html_theme_options.get("secondary_accent")
    if accent is not True:
        return accent or None
    if pkg := packages.get(_package_name(config)):
        return pkg.secondary_accent
    return None


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
    # In source trees, rebuild the stylesheet bundles so edits show without reinstalling.
    if exe := find_lightningcss():
        bundle(exe)

    css = _ACCENT_CSS.format(accent=_accent(config))
    if secondary := _secondary_accent(config):
        css += _SECONDARY_ACCENT_CSS.format(accent=secondary)
    static_dir = _build_cache(app) / "static"
    static_dir.mkdir(parents=True, exist_ok=True)
    (static_dir / "scverse-accent.css").write_text(css)
    config.html_static_path = [*config.html_static_path, str(static_dir)]
    app.add_css_file("scverse-accent.css")
    app.add_js_file("scripts/readthedocs-integration.js", type="module")


def _add_ecosystem_context(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, object],
    doctree: object,
) -> None:
    """Expose the registry to the scverse menu template."""
    if app.config.html_theme != "scverse":
        return
    current = _package_name(app.config).lower()
    groups: dict[str, list[dict[str, object]]] = {"core": [], "ecosystem": []}
    for pkg in packages.values():
        groups[pkg.kind].append({"name": pkg.name, "docs": pkg.docs, "current": pkg.name.lower() == current})
    context["scverse_ecosystem"] = groups


def _keep_sections_with_toctrees(tree: nodes.Element) -> None:
    """Drop section entries without a toctree below them; turn the rest into captions.

    `pydata-sphinx-theme` removes every entry linking to an anchor, so the kept ones must not be links.
    """
    # Bottom-up, so emptied sub-lists are gone before their parents are checked.
    for item in reversed(list(tree.findall(nodes.list_item))):
        ref, *descendants = item.findall(nodes.reference)
        if not ref["anchorname"]:
            continue
        if any(not r["anchorname"] for r in descendants):
            ref.parent.replace_self(nodes.paragraph("", "", *ref.children, classes=["caption"]))
            continue
        ul = item.parent
        ul.remove(item)
        if not ul.children:
            ul.parent.remove(ul)


def _with_section_caption(toctree: addnodes.toctree) -> addnodes.toctree:
    """Caption a toctree with its section’s title, unless it has a caption or isn’t in a subsection.

    Only used on the root page, whose sections Sphinx otherwise leaves out of the global toctree.
    Copies the node when it changes it, as the root doctree is cached.
    """
    section = toctree.parent
    while section is not None and not isinstance(section, nodes.section):
        section = section.parent
    if toctree.get("caption") or section is None or not isinstance(section.parent, nodes.section):
        return toctree  # the page title isn’t a caption
    toctree = toctree.copy()
    toctree["caption"] = toctree["rawcaption"] = section[0].astext()  # a section starts with its title
    return toctree


def _add_section_toctree(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: _PageContext,
    doctree: object,
) -> None:
    """Let ``toctree(sections_with_toctrees=True)`` keep page sections that contain toctrees."""
    toctree = context.get("toctree")
    builder = app.builder
    if app.config.html_theme != "scverse" or toctree is None or not isinstance(builder, StandaloneHTMLBuilder):
        return

    def section_toctree(
        *,
        sections_with_toctrees: bool = False,
        collapse: bool = True,
        maxdepth: int = 0,
        includehidden: bool = False,
        **kwargs: bool,
    ) -> str:
        if not sections_with_toctrees:
            return toctree(collapse=collapse, maxdepth=maxdepth, includehidden=includehidden, **kwargs)
        resolve = partial(
            _resolve_toctree,
            app.env,
            pagename,
            builder,
            prune=True,
            maxdepth=maxdepth,
            titles_only=False,
            collapse=collapse,
            includehidden=includehidden,
            tags=app.tags,
        )
        toctrees = map(_with_section_caption, app.env.master_doctree.findall(addnodes.toctree))
        resolved = [t for t in map(resolve, toctrees) if t is not None]
        # Like `global_toctree_for_doc`, but root-page sections are only visible in toctree captions.
        if not resolved:
            return ""
        tree, *rest = resolved
        tree.extend(child for t in rest for child in t.children)
        _keep_sections_with_toctrees(tree)
        return builder.render_partial(tree)["fragment"]

    context["toctree"] = section_toctree


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the theme, its templates, and the build hooks."""
    app.add_html_theme("scverse", str(_THEME_PATH))
    app.config.templates_path = [*app.config.templates_path, str(_THEME_PATH / "components")]
    app.setup_extension("scverse_doc.source")

    app.connect("builder-inited", _configure)
    app.connect("html-page-context", _add_ecosystem_context)
    app.connect("html-page-context", _add_section_toctree)

    return ExtensionMetadata(parallel_read_safe=True)
