# SPDX-License-Identifier: MPL-2.0
"""Contrast guarantees for the derived accents."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from coloraide import Color

from scverse_doc.registry import DEFAULT_ACCENT, packages
from scverse_doc.theme import (
    _DARK_BACKGROUND,
    _LIGHT_BACKGROUND,
    _MAX_LIGHTNESS_ON_LIGHT,
    _MIN_LIGHTNESS_ON_DARK,
    _accent,
    _secondary_accent,
)

#: Minimum contrast ratio for normal-size body text under WCAG 2.1 AA.
WCAG_AA_NORMAL = 4.5

ACCENTS = sorted({a for pkg in packages.values() for a in (pkg.accent, pkg.secondary_accent) if a})


def contrast(color: Color, background: str) -> float:
    """WCAG contrast of `color` as a browser shows it: gamut-mapped to sRGB by reducing OKLCH chroma."""
    return color.clone().fit("srgb", method="oklch-chroma").contrast(background, method="wcag21")


@pytest.mark.parametrize(
    ("lightness", "background"),
    [
        pytest.param(_MAX_LIGHTNESS_ON_LIGHT, _LIGHT_BACKGROUND, id="light"),
        pytest.param(_MIN_LIGHTNESS_ON_DARK, _DARK_BACKGROUND, id="dark"),
    ],
)
def test_lightness_bound_meets_aa_for_any_hue(lightness: float, background: str) -> None:
    failing = [
        (chroma, hue)
        for hue in range(0, 360, 2)
        for chroma in (c / 100 for c in range(0, 41, 2))
        if contrast(Color("oklch", [lightness, chroma, hue]), background) < WCAG_AA_NORMAL
    ]
    assert not failing


def test_bounds_are_load_bearing() -> None:
    """Several brand accents fail AA unmodified, which is why they are never used as link colours."""
    assert [a for a in ACCENTS if Color(a).contrast(_LIGHT_BACKGROUND, method="wcag21") < WCAG_AA_NORMAL]


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        pytest.param({}, DEFAULT_ACCENT, id="unknown"),
        pytest.param({"accent": "#c0f"}, "#c0f", id="declared"),
    ],
)
def test_accent_for_a_package_outside_the_registry(options: dict[str, str], expected: str) -> None:
    config = SimpleNamespace(html_theme_options=options, project="not-an-scverse-package")
    assert _accent(config) == expected  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("project", "options", "expected"),
    [
        pytest.param("pertpy", {}, None, id="unset"),
        pytest.param("pertpy", {"secondary_accent": True}, "oklch(0.595 0.177 14)", id="registry"),
        pytest.param("anndata", {"secondary_accent": True}, None, id="single-colour"),
        pytest.param("not-an-scverse-package", {"secondary_accent": True}, None, id="unknown"),
        pytest.param("pertpy", {"secondary_accent": "#c0f"}, "#c0f", id="declared"),
    ],
)
def test_secondary_accent(project: str, options: dict[str, str], expected: str | None) -> None:
    config = SimpleNamespace(html_theme_options=options, project=project)
    assert _secondary_accent(config) == expected  # type: ignore[arg-type]
