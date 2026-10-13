"""End-to-end builds of the fixture documentation trees."""

from __future__ import annotations

from importlib.util import find_spec
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sphinx.application import Sphinx
from sphinx.environment import CONFIG_OK

from scverse_doc.config import DEFAULTS

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOTS = Path(__file__).parent / "roots"

#: Roots listing ``scverse_doc`` need both extras; one module stands in for each.
needs_full = pytest.mark.skipif(
    find_spec("myst_nb") is None or find_spec("pydata_sphinx_theme") is None, reason="needs scverse-doc[full]"
)


def build(root: Path, out: Path, *, freshenv: bool = True, **overrides: object) -> tuple[Sphinx, str]:
    """Build `root` into `out` and return the app and the rendered index page."""
    app, _ = build_capturing_warnings(root, out, freshenv=freshenv, **overrides)
    return app, (out / "html" / "index.html").read_text()


def build_capturing_warnings(
    root: Path, out: Path, *, freshenv: bool = True, **overrides: object
) -> tuple[Sphinx, str]:
    """Build `root` into `out` and return the app and everything it wrote to the warning stream."""
    warnings = StringIO()
    app = Sphinx(
        srcdir=str(root),
        confdir=str(root),
        outdir=str(out / "html"),
        doctreedir=str(out / "doctrees"),
        buildername="html",
        confoverrides={"intersphinx_mapping": {}, "nitpicky": False, **overrides},
        warning=warnings,
        freshenv=freshenv,
    )
    app.build()
    return app, warnings.getvalue()


@pytest.fixture(scope="module")
def minimal(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Sphinx, str]]:
    yield build(ROOTS / "minimal", tmp_path_factory.mktemp("minimal"))


@needs_full
def test_theme_renders_the_shared_chrome(minimal: tuple[Sphinx, str]) -> None:
    app, html = minimal
    assert app.config.html_theme == "scverse"
    for css in ("styles/scverse.css", "scverse-accent.css"):
        assert css in html
    assert "NumFOCUS" in html
    assert "github.com/scverse/pertpy/edit/main/docs/index.md" in html
    assert 'href="https://github.com/scverse/pertpy"' in html


@needs_full
def test_linkcode_is_resolved_when_requested(minimal: tuple[Sphinx, str]) -> None:
    app, _ = minimal
    assert callable(app.config.linkcode_resolve)
    assert app.config.linkcode_resolve("py", {"module": "scverse_doc.registry", "fullname": "Package"}).startswith(
        "https://github.com/scverse/pertpy/blob/main/src/scverse_doc/registry.py#L"
    )


@needs_full
def test_ecosystem_dropdown_is_built_from_the_registry(minimal: tuple[Sphinx, str]) -> None:
    _, html = minimal
    # Display names are the upstream ``name`` verbatim, inconsistent casing and all.
    assert ">AnnData</a>" in html
    assert ">annsel</a>" in html
    assert 'class="dropdown-item active"' in html


@needs_full
def test_accent_is_derived_for_both_modes(minimal: tuple[Sphinx, str]) -> None:
    app, _ = minimal
    css = (Path(app.outdir) / "_static" / "scverse-accent.css").read_text()
    assert "--scverse-color-accent-decorative: #da347f;" in css
    assert "--scverse-color-accent-text: light-dark(#" in css


@needs_full
def test_build_is_warning_free(tmp_path: Path) -> None:
    _, warnings = build_capturing_warnings(ROOTS / "minimal", tmp_path)
    # Building several Sphinx apps in one process re-registers nodes and directives; that noise is the harness.
    real = [line for line in warnings.splitlines() if line.strip() and "is already registered" not in line]
    assert real == []


@needs_full
def test_rebuilding_reuses_everything(tmp_path: Path) -> None:
    """The config we inject must hash the same next build, or every page is written again."""
    build(ROOTS / "minimal", tmp_path)
    buildinfo = (tmp_path / "html" / ".buildinfo").read_text()

    app, _ = build(ROOTS / "minimal", tmp_path, freshenv=False)
    assert (tmp_path / "html" / ".buildinfo").read_text() == buildinfo
    assert app.env.config_status == CONFIG_OK
    assert list(app.builder.get_outdated_docs()) == []


@needs_full
def test_theme_works_without_being_listed_as_an_extension(tmp_path: Path) -> None:
    """Selecting the theme loads it from the entry point, which happens after ``config-inited``."""
    app, html = build(ROOTS / "entry-point", tmp_path)
    assert "scverse_doc.theme" in app.extensions
    assert "scverse-accent.css" in html
    assert "scverse-ecosystem-dropdown" in html
    assert "scverse_doc.source" in app.extensions
    assert "github.com/scverse/pertpy/edit/main/docs/index.rst" in html
    assert callable(app.config.linkcode_resolve)


@needs_full
@pytest.mark.parametrize("theme", ["furo", "sphinx_book_theme"])
def test_source_links_reach_other_themes(tmp_path: Path, theme: str) -> None:
    """The names `scverse_doc.source` fills in are the ones these themes really read."""
    _, html = build(ROOTS / "minimal", tmp_path, html_theme=theme, html_theme_options={})
    assert "github.com/scverse/pertpy/edit/main/docs/index.md" in html


@needs_full
def test_conf_py_can_pick_another_theme(tmp_path: Path) -> None:
    """A theme that declares none of the source options must not be given any."""
    app, _ = build(ROOTS / "minimal", tmp_path, html_theme="alabaster")
    assert app.config.html_theme == "alabaster"
    assert app.config.html_theme_options.keys() == {"announcement"}


@needs_full
def test_conf_py_wins_over_defaults(tmp_path: Path) -> None:
    app, html = build(ROOTS / "override", tmp_path)
    assert app.config.nb_execution_mode == "force"
    assert app.config.html_theme_options["show_toc_level"] == 4
    assert app.config.napoleon_numpy_docstring is DEFAULTS["napoleon_numpy_docstring"]
    # "not-an-scverse-package" is not in the registry, which must not break the theme.
    assert "scverse-ecosystem-dropdown" in html


@pytest.fixture(scope="module")
def autodoc(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("autodoc")
    build(ROOTS / "autodoc", out)
    return out / "html"


def test_autodoc_works_without_the_theme(autodoc: Path) -> None:
    assert "scverse" not in (autodoc / "index.html").read_text()


def test_class_template_documents_members_by_kind(autodoc: Path) -> None:
    html = (autodoc / "generated" / "apimod.Thing.html").read_text()
    assert "Attributes table" in html
    assert "Methods table" in html
    assert 'class="py property"' in html
    assert 'class="py method"' in html
    assert 'class="py attribute"' in html


def test_private_bases_are_hidden(autodoc: Path) -> None:
    html = (autodoc / "generated" / "apimod.Thing.html").read_text()
    assert "Bases:" in html
    assert "Public" in html
    assert "_Private" not in html
    assert "Generic" not in html


def test_prose_returns(autodoc: Path) -> None:
    html = (autodoc / "generated" / "apimod.fit.html").read_text()
    assert "<p>The fitted model, or <cite>None</cite>" in html
    # Unpatched napoleon would read the sentence as a type.
    assert "Return type" not in html
