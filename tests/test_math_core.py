# SPDX-License-Identifier: MPL-2.0
"""Math rendered to MathML, with Sphinx’s equation numbers and error fallback."""

from __future__ import annotations

import re

import pytest
from sphinx.testing.util import SphinxTestApp

pytest.importorskip("math_core")


@pytest.fixture(scope="module")
def build(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    """Build a page with inline, labelled and broken math, and return its HTML and warnings."""
    srcdir = tmp_path_factory.mktemp("math_core")
    (srcdir / "conf.py").write_text('extensions = ["scverse_doc.math_core"]\n')
    (srcdir / "index.rst").write_text(
        r"""Inline :math:`a^2`, see :eq:`foo`.

.. math:: e = mc^2
   :label: foo

.. math:: x<\frac{a

.. math::

   p &= q

   r &= s

.. math::
   :no-wrap:

   \begin{cases} 1 \\ 0 \end{cases}
"""
    )
    app = SphinxTestApp("html", srcdir=srcdir)
    try:
        app.build()
    finally:
        app.cleanup()
    assert (app.outdir / "_static" / "math_core.css").is_file()
    return (app.outdir / "index.html").read_text(), app.warning.getvalue()


def test_inline(build: tuple[str, str]) -> None:
    html, _ = build
    assert "<math><msup><mi>a</mi><mn>2</mn></msup></math>" in html


def test_label(build: tuple[str, str]) -> None:
    html, _ = build
    assert '<a class="reference internal" href="#equation-foo">(1)</a>' in html
    assert '<div class="math" id="equation-foo">\n<span class="eqno">(1)' in html
    assert '<math display="block">' in html


def test_error(build: tuple[str, str]) -> None:
    html, warnings = build
    assert "index.rst:6: WARNING: LaTeX error:" in warnings
    assert 'class="math-core-error"' in html
    assert r"<code>x&lt;\frac{a" in html


def test_css(build: tuple[str, str]) -> None:
    html, _ = build
    assert 'href="_static/math_core.css' in html


def test_wrap(build: tuple[str, str]) -> None:
    html, warnings = build
    # both equations in one `aligned` table, without numbers
    [block] = re.findall(r"<math[^>]*>(?:(?!</math>).)*<mi>p</mi>.*?</math>", html)
    assert "<mi>r</mi>" in block
    assert "<mtext>(" not in html
    assert warnings.count("LaTeX error") == 1  # broken \frac


def test_no_wrap(build: tuple[str, str]) -> None:
    html, _ = build
    assert '<mo stretchy="true">{</mo>' in html or "<mo>{</mo>" in html
