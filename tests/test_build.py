"""End-to-end builds of the fixture documentation trees."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from sphinx.application import Sphinx

from scverse_doc.config import DEFAULTS

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOTS = Path(__file__).parent / "roots"


def build(root: Path, out: Path, **overrides: object) -> tuple[Sphinx, str]:
    """Build `root` into `out` and return the app and the rendered index page."""
    app, _ = build_capturing_warnings(root, out, **overrides)
    return app, (out / "html" / "index.html").read_text()


def build_capturing_warnings(root: Path, out: Path, **overrides: object) -> tuple[Sphinx, str]:
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
        freshenv=True,
    )
    app.build()
    return app, warnings.getvalue()


@pytest.fixture(scope="module")
def minimal(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Sphinx, str]]:
    yield build(ROOTS / "minimal", tmp_path_factory.mktemp("minimal"))


def test_theme_resolves(minimal: tuple[Sphinx, str]) -> None:
    app, _ = minimal
    assert app.config.html_theme == "scverse"


def test_brand_stylesheets_are_linked(minimal: tuple[Sphinx, str]) -> None:
    _, html = minimal
    for css in ("styles/scverse.css", "scverse-accent.css", "scverse-dark.css"):
        assert css in html


def test_accent_stylesheet_derives_both_modes(minimal: tuple[Sphinx, str]) -> None:
    app, _ = minimal
    css = (Path(app.outdir) / "_static" / "scverse-accent.css").read_text()
    assert "--scverse-color-accent-decorative: #da347f;" in css
    assert css.count("--scverse-color-accent-text") == 2


def test_ecosystem_dropdown_lists_the_registry(minimal: tuple[Sphinx, str]) -> None:
    _, html = minimal
    assert "scverse-ecosystem-dropdown" in html
    assert ">anndata</a>" in html
    assert ">annsel</a>" in html


def test_current_package_is_marked(minimal: tuple[Sphinx, str]) -> None:
    _, html = minimal
    assert 'class="dropdown-item active"' in html


def test_footer_carries_the_shared_boilerplate(minimal: tuple[Sphinx, str]) -> None:
    _, html = minimal
    assert "NumFOCUS" in html
    assert "discourse.scverse.org" in html


def test_edit_button_is_derived_from_repo(minimal: tuple[Sphinx, str]) -> None:
    _, html = minimal
    assert "github.com/scverse/pertpy/edit/main/docs/index.md" in html


def test_config_layer_produces_no_warnings(tmp_path: Path) -> None:
    _, warnings = build_capturing_warnings(ROOTS / "minimal", tmp_path)
    # Building several Sphinx apps in one process re-registers nodes and directives; that noise is the harness.
    real = [line for line in warnings.splitlines() if line.strip() and "is already registered" not in line]
    assert real == []


def test_defaults_are_applied(minimal: tuple[Sphinx, str]) -> None:
    app, _ = minimal
    assert app.config.napoleon_numpy_docstring is True
    assert app.config.nb_execution_mode == "off"


def test_conf_py_wins_over_defaults(tmp_path: Path) -> None:
    app, _ = build(ROOTS / "override", tmp_path)
    assert app.config.nb_execution_mode == "force"
    assert app.config.html_theme_options["show_toc_level"] == 4
    assert app.config.napoleon_numpy_docstring is DEFAULTS["napoleon_numpy_docstring"]


def test_theme_works_without_a_registry_entry(tmp_path: Path) -> None:
    app, html = build(ROOTS / "override", tmp_path / "unregistered")
    assert app.config.html_theme == "scverse"
    assert "scverse-ecosystem-dropdown" in html
