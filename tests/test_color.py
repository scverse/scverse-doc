# SPDX-License-Identifier: MPL-2.0
"""Contrast guarantees for the derived accents."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scverse_doc._color import WCAG_AA_NORMAL, contrast_ratio, derive_readable, parse_hex
from scverse_doc.registry import DEFAULT_ACCENT, packages
from scverse_doc.theme import _DARK_BACKGROUND, _LIGHT_BACKGROUND, _accent

ACCENTS = sorted({pkg.accent for pkg in packages.values()})


def test_every_derived_accent_meets_aa() -> None:
    for accent in ACCENTS:
        for background in (_LIGHT_BACKGROUND, _DARK_BACKGROUND):
            derived = derive_readable(accent, background)
            assert contrast_ratio(derived, background) >= WCAG_AA_NORMAL, (accent, background, derived)


def test_derivation_is_load_bearing() -> None:
    """Several brand accents fail AA unmodified, which is why they are never used as link colours."""
    assert [a for a in ACCENTS if contrast_ratio(a, _LIGHT_BACKGROUND) < WCAG_AA_NORMAL]


def test_readable_accent_is_left_alone() -> None:
    assert derive_readable("#000000", _LIGHT_BACKGROUND) == "#000000"


def test_short_hex_is_expanded() -> None:
    """Users can write ``accent = "#c0f"`` in ``html_theme_options``."""
    assert parse_hex("#c0f") == parse_hex("#cc00ff")


def test_garbage_is_rejected() -> None:
    with pytest.raises(ValueError, match="Not a hex colour"):
        parse_hex("nope")


@pytest.mark.parametrize(("background", "expected"), [("#ffffff", "#000000"), ("#000000", "#ffffff")])
def test_unreachable_target_falls_back_to_the_extreme(background: str, expected: str) -> None:
    assert derive_readable("#808080", background, target=22) == expected


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
