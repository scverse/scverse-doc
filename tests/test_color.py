"""Contrast guarantees for the derived accents."""

from __future__ import annotations

import pytest

from scverse_doc._color import WCAG_AA_NORMAL, contrast_ratio, derive_readable, parse_hex, relative_luminance
from scverse_doc._ext import DARK_BACKGROUND, LIGHT_BACKGROUND
from scverse_doc.registry import packages

ACCENTS = sorted({pkg.accent for pkg in packages().values()})


@pytest.mark.parametrize("background", [LIGHT_BACKGROUND, DARK_BACKGROUND])
@pytest.mark.parametrize("accent", ACCENTS)
def test_derived_accent_meets_aa(accent: str, background: str) -> None:
    assert contrast_ratio(derive_readable(accent, background), background) >= WCAG_AA_NORMAL


def test_raw_accents_would_not_all_pass() -> None:
    """The derivation is load-bearing, not decorative: several brand accents fail AA unmodified."""
    failing = [a for a in ACCENTS if contrast_ratio(a, LIGHT_BACKGROUND) < WCAG_AA_NORMAL]
    assert failing


def test_readable_accent_is_left_alone() -> None:
    assert derive_readable("#000000", LIGHT_BACKGROUND) == "#000000"


@pytest.mark.parametrize(
    ("text", "expected"),
    [("#fff", (1.0, 1.0, 1.0)), ("000000", (0.0, 0.0, 0.0)), ("#4557C4", (69 / 255, 87 / 255, 196 / 255))],
)
def test_parse_hex(text: str, expected: tuple[float, float, float]) -> None:
    assert parse_hex(text) == pytest.approx(expected)


def test_parse_hex_rejects_junk() -> None:
    with pytest.raises(ValueError, match="Not a hex colour"):
        parse_hex("rebeccapurple")


def test_known_contrast_ratios() -> None:
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert relative_luminance("#ffffff") == pytest.approx(1.0)
