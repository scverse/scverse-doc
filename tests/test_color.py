"""Contrast guarantees for the derived accents."""

from __future__ import annotations

from scverse_doc._color import WCAG_AA_NORMAL, contrast_ratio, derive_readable, parse_hex
from scverse_doc._ext import DARK_BACKGROUND, LIGHT_BACKGROUND
from scverse_doc.registry import packages

ACCENTS = sorted({pkg.accent for pkg in packages.values()})


def test_every_derived_accent_meets_aa() -> None:
    for accent in ACCENTS:
        for background in (LIGHT_BACKGROUND, DARK_BACKGROUND):
            derived = derive_readable(accent, background)
            assert contrast_ratio(derived, background) >= WCAG_AA_NORMAL, (accent, background, derived)


def test_derivation_is_load_bearing() -> None:
    """Several brand accents fail AA unmodified, which is why they are never used as link colours."""
    assert [a for a in ACCENTS if contrast_ratio(a, LIGHT_BACKGROUND) < WCAG_AA_NORMAL]


def test_readable_accent_is_left_alone() -> None:
    assert derive_readable("#000000", LIGHT_BACKGROUND) == "#000000"


def test_short_hex_is_expanded() -> None:
    """Users can write ``accent = "#c0f"`` in ``html_theme_options``."""
    assert parse_hex("#c0f") == parse_hex("#cc00ff")
