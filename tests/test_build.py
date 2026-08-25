"""End-to-end builds of the fixture documentation trees."""

from __future__ import annotations

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


def test_theme_renders_the_shared_chrome(minimal: tuple[Sphinx, str]) -> None:
    app, html = minimal
    assert app.config.html_theme == "scverse"
    for css in ("styles/scverse.css", "scverse-accent.css"):
        assert css in html
    assert "NumFOCUS" in html
    assert "github.com/scverse/pertpy/edit/main/docs/index.md" in html


def test_ecosystem_dropdown_is_built_from_the_registry(minimal: tuple[Sphinx, str]) -> None:
    _, html = minimal
    # Display names are the upstream ``name`` verbatim, inconsistent casing and all.
    assert ">AnnData</a>" in html
    assert ">annsel</a>" in html
    assert 'class="dropdown-item active"' in html


def test_accent_is_derived_for_both_modes(minimal: tuple[Sphinx, str]) -> None:
    app, _ = minimal
    css = (Path(app.outdir) / "_static" / "scverse-accent.css").read_text()
    assert "--scverse-color-accent-decorative: #da347f;" in css
    assert "--scverse-color-accent-text: light-dark(#" in css


def test_build_is_warning_free(tmp_path: Path) -> None:
    _, warnings = build_capturing_warnings(ROOTS / "minimal", tmp_path)
    # Building several Sphinx apps in one process re-registers nodes and directives; that noise is the harness.
    real = [line for line in warnings.splitlines() if line.strip() and "is already registered" not in line]
    assert real == []


def test_rebuilding_reuses_everything(tmp_path: Path) -> None:
    """The config we inject must hash the same next build, or every page is written again."""
    build(ROOTS / "minimal", tmp_path)
    buildinfo = (tmp_path / "html" / ".buildinfo").read_text()

    app, _ = build(ROOTS / "minimal", tmp_path, freshenv=False)
    assert (tmp_path / "html" / ".buildinfo").read_text() == buildinfo
    assert app.env.config_status == CONFIG_OK
    assert list(app.builder.get_outdated_docs()) == []


def test_conf_py_wins_over_defaults(tmp_path: Path) -> None:
    app, html = build(ROOTS / "override", tmp_path)
    assert app.config.nb_execution_mode == "force"
    assert app.config.html_theme_options["show_toc_level"] == 4
    assert app.config.napoleon_numpy_docstring is DEFAULTS["napoleon_numpy_docstring"]
    # "not-an-scverse-package" is not in the registry, which must not break the theme.
    assert "scverse-ecosystem-dropdown" in html
