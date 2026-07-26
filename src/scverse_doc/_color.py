"""Colour maths for deriving accessible accent shades.

Package accents are chosen for brand recognition, not for contrast.
Several of the accents scverse already uses (``#6cf1a1`` for muon, ``#fbb822`` for scvi-tools) fail WCAG AA as text
colours on white, and others fail on a dark background.
So the raw accent is only ever used for decorative surfaces, and text/link colours are *derived* from it here by
moving lightness until the contrast target is met, keeping hue and saturation intact so the result still reads as the
package's colour.
"""

from __future__ import annotations

import re
from typing import NamedTuple

__all__ = ["contrast_ratio", "derive_readable", "parse_hex", "relative_luminance"]

#: Minimum contrast ratio for normal-size body text under WCAG 2.1 AA.
WCAG_AA_NORMAL = 4.5

#: Minimum contrast ratio for large text and non-text UI components under WCAG 2.1 AA.
WCAG_AA_LARGE = 3.0

_HEX_RE = re.compile(r"\A#?(?P<digits>[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")


class RGB(NamedTuple):
    """An sRGB colour with channels in ``[0, 1]``."""

    r: float
    g: float
    b: float

    def to_hex(self) -> str:
        """Render as a lowercase ``#rrggbb`` string."""
        return "#" + "".join(f"{round(c * 255):02x}" for c in self)


def parse_hex(color: str) -> RGB:
    """Parse a CSS hex colour.

    Parameters
    ----------
    color
        A ``#rgb`` or ``#rrggbb`` string, with or without the leading ``#``.

    Returns
    -------
    The colour, with channels normalised to ``[0, 1]``.

    Raises
    ------
    ValueError
        If `color` is not a three- or six-digit hex colour.
    """
    if (m := _HEX_RE.match(color.strip())) is None:
        msg = f"Not a hex colour: {color!r}"
        raise ValueError(msg)
    digits = m["digits"]
    if len(digits) == 3:
        digits = "".join(d * 2 for d in digits)
    return RGB(*(int(digits[i : i + 2], 16) / 255 for i in (0, 2, 4)))


def _to_linear(channel: float) -> float:
    """Undo the sRGB transfer function for a single channel."""
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(color: RGB | str) -> float:
    """Compute the WCAG relative luminance of a colour.

    Parameters
    ----------
    color
        An :class:`RGB` colour or a hex string.

    Returns
    -------
    Relative luminance in ``[0, 1]``, where 0 is black and 1 is white.
    """
    r, g, b = parse_hex(color) if isinstance(color, str) else color
    return 0.2126 * _to_linear(r) + 0.7152 * _to_linear(g) + 0.0722 * _to_linear(b)


def contrast_ratio(fg: RGB | str, bg: RGB | str) -> float:
    """Compute the WCAG contrast ratio between two colours.

    Parameters
    ----------
    fg
        Foreground colour.
    bg
        Background colour.

    Returns
    -------
    A ratio between 1 (identical) and 21 (black on white).
    """
    lum_a, lum_b = relative_luminance(fg), relative_luminance(bg)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _to_hsl(color: RGB) -> tuple[float, float, float]:
    """Convert sRGB to HSL, with hue in degrees and the rest in ``[0, 1]``."""
    r, g, b = color
    high, low = max(r, g, b), min(r, g, b)
    lightness = (high + low) / 2
    if high == low:
        return 0.0, 0.0, lightness
    delta = high - low
    saturation = delta / (2 - high - low) if lightness > 0.5 else delta / (high + low)
    match high:
        case _ if high == r:
            hue = ((g - b) / delta) % 6
        case _ if high == g:
            hue = (b - r) / delta + 2
        case _:
            hue = (r - g) / delta + 4
    return hue * 60, saturation, lightness


def _from_hsl(hue: float, saturation: float, lightness: float) -> RGB:
    """Convert HSL back to sRGB."""
    chroma = (1 - abs(2 * lightness - 1)) * saturation
    secondary = chroma * (1 - abs((hue / 60) % 2 - 1))
    offset = lightness - chroma / 2
    match hue % 360:
        case h if h < 60:
            triple = (chroma, secondary, 0.0)
        case h if h < 120:
            triple = (secondary, chroma, 0.0)
        case h if h < 180:
            triple = (0.0, chroma, secondary)
        case h if h < 240:
            triple = (0.0, secondary, chroma)
        case h if h < 300:
            triple = (secondary, 0.0, chroma)
        case _:
            triple = (chroma, 0.0, secondary)
    return RGB(*(c + offset for c in triple))


def derive_readable(accent: str, background: str, *, target: float = WCAG_AA_NORMAL) -> str:
    """Derive a text-safe variant of `accent` that meets `target` contrast against `background`.

    Hue and saturation are preserved and only lightness is moved, so the result still reads as the same colour.
    Lightness moves away from the background: darker on a light background, lighter on a dark one.

    Parameters
    ----------
    accent
        The brand accent to adjust, as a hex string.
    background
        The background the derived colour will sit on, as a hex string.
    target
        The contrast ratio to reach.

    Returns
    -------
    A hex colour meeting `target` where that is achievable by lightness alone, otherwise the closest achievable
    colour, which is black or white.

    Examples
    --------
    >>> derive_readable("#fbb822", "#ffffff")  # scvi-tools yellow, unreadable as-is
    '#9d6d03'
    """
    if contrast_ratio(accent, background) >= target:
        return parse_hex(accent).to_hex()

    hue, saturation, lightness = _to_hsl(parse_hex(accent))
    darken = relative_luminance(background) > 0.5
    step = -1 / 512 if darken else 1 / 512

    # Candidates are checked after rounding to 8-bit hex: a float lightness that clears the target can fall back
    # under it once quantized, which is how #e5864b and #fbb822 ended up one hundredth short of AA.
    while 0.0 <= (lightness := lightness + step) <= 1.0:
        candidate = parse_hex(_from_hsl(hue, saturation, lightness).to_hex())
        if contrast_ratio(candidate, background) >= target:
            return candidate.to_hex()

    return "#000000" if darken else "#ffffff"
