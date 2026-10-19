# SPDX-License-Identifier: MPL-2.0
"""Overridden qualnames and guarded imports in annotations."""

from __future__ import annotations

import sys
from textwrap import dedent
from typing import TYPE_CHECKING

import pytest
from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from pathlib import Path

MODULE = '''\
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fractions import Fraction
    from does_not_exist import Nothing


class _Private:
    """Documented as Public."""


Public = _Private


def f(a: Fraction, b: _Private) -> None:
    """Use both."""
'''


@pytest.fixture
def build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str, str]:
    """Build a page documenting :data:`MODULE`, and return its HTML, status, and warnings."""
    (tmp_path / "qo_mod.py").write_text(MODULE)
    (tmp_path / "conf.py").write_text(
        dedent("""\
        extensions = ["scverse_doc.xref_overrides"]
        nitpicky = True
        xref_overrides = {"qo_mod._Private": "qo_mod.Public", "qo_mod.Unused": "qo_mod.Public"}
        """)
    )
    (tmp_path / "index.rst").write_text(".. autoclass:: qo_mod.Public\n\n.. autofunction:: qo_mod.f\n")
    monkeypatch.syspath_prepend(tmp_path)
    monkeypatch.delitem(sys.modules, "qo_mod", raising=False)
    app = SphinxTestApp("html", srcdir=tmp_path)
    try:
        app.build()
    finally:
        app.cleanup()
    return (app.outdir / "index.html").read_text(), app.status.getvalue(), app.warning.getvalue()


def test_override(build: tuple[str, str, str]) -> None:
    html, _, warnings = build
    assert 'href="#qo_mod.Public"' in html
    assert "_Private" not in warnings


def test_guarded_import(build: tuple[str, str, str]) -> None:
    _, _, warnings = build
    # resolved to the full name (there’s no inventory to link it to)
    assert "reference target not found: fractions.Fraction" in warnings


def test_deprecated_name(tmp_path: Path) -> None:
    (tmp_path / "conf.py").write_text('extensions = ["scverse_doc.xref_overrides"]\nqualname_overrides = {"a": "b"}\n')
    app = SphinxTestApp("html", srcdir=tmp_path)
    app.cleanup()
    assert app.config.xref_overrides == {"a": "b"}
    assert "`qualname_overrides` is deprecated" in app.warning.getvalue()


def test_unused(build: tuple[str, str, str]) -> None:
    _, status, _ = build
    assert "note: unused xref_overrides entry qo_mod.Unused" in status
    assert "qo_mod._Private" not in status
