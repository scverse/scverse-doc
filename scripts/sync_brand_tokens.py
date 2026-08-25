#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Refresh the generated brand assets from the scverse website.

The website is the brand’s source of truth,
so transcribing its hex values into this repository by hand
would create exactly the kind of drift this package exists to remove.
This script extracts the handful of SCSS variables that make up the brand
and writes them into ``_tokens.css`` as ``--scverse-color-x-light`` values.

Only the region between the marker comments is touched; it holds upstream hex values and nothing else.
The rest of the file is hand-authored – including the ``light-dark()`` tokens that pair each generated
light value with a dark one, because the website has no dark mode to extract those from.

The scverse logo used for the navbar link back to the website is copied verbatim for the same reason.

Usage
-----
    uv run scripts/sync_brand_tokens.py --website ../scverse.github.io
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
STATIC = HERE.parent / "src" / "scverse_doc" / "theme" / "scverse" / "static"
TARGET = STATIC / "_tokens.css"

#: Website file -> theme static file, copied verbatim.
ASSETS = {Path("static/img/logo/scverse-fa.svg"): STATIC / "scverse-fa.svg"}

#: SCSS variable in ``assets/main.scss`` -> CSS custom property emitted here.
TOKEN_MAP = {
    "greyheader": "--scverse-color-heading",
    "navtext": "--scverse-color-text-secondary",
    "greydesc": "--scverse-color-text-muted",
    "tilebg": "--scverse-color-surface",
    "tilebg4": "--scverse-color-surface-alt",
    "overline": "--scverse-color-border",
    "backtickbg": "--scverse-color-code-bg",
    "tiletext": "--scverse-color-code-text",
    "footerbg": "--scverse-color-footer-bg",
}

#: Values that are written as literals in the SCSS rather than as variables,
#: so they cannot be looked up by name.
#: Verified against ``assets/main.scss`` by :func:`check_literals`.
LITERALS = {
    "--scverse-color-primary": "#4557c4",
    "--scverse-color-gradient-start": "#262fb5",
    "--scverse-color-gradient-end": "#74c8fa",
}

BEGIN = "/* BEGIN GENERATED BRAND TOKENS – DO NOT EDIT; regenerate with scripts/sync_brand_tokens.py */"
END = "/* END GENERATED BRAND TOKENS */"

#: The fenced region, captured together with the indentation of its opening marker.
REGION_RE = re.compile(rf"^([ \t]*){re.escape(BEGIN)}\n.*?^[ \t]*{re.escape(END)}$", re.DOTALL | re.MULTILINE)


def parse_scss(scss: str) -> dict[str, str]:
    """Extract top-level ``$name: #value;`` declarations from SCSS source."""
    return dict(re.findall(r"^\$([\w-]+):\s*(#[0-9a-fA-F]{3,8})\s*;", scss, re.MULTILINE))


def check_literals(scss: str) -> list[str]:
    """Return the literal token values that no longer appear in the SCSS.

    The primary and the gradient stops are written inline in the website’s CSS rules,
    so they cannot be resolved by variable name.
    Checking that they still occur at all is a cheap guard against the brand changing underneath us.
    """
    return [f"{name} ({value})" for name, value in LITERALS.items() if value.lower() not in scss.lower()]


def render_region(scss: str, indent: str) -> str:
    """Render the generated region – marker comments included – indented by `indent`."""
    variables = parse_scss(scss)
    if missing := sorted(set(TOKEN_MAP) - set(variables)):
        msg = f"SCSS variables vanished from the website: {', '.join('$' + m for m in missing)}"
        raise KeyError(msg)

    values = {**LITERALS, **{prop: variables[scss_name] for scss_name, prop in TOKEN_MAP.items()}}
    lines = [BEGIN, *(f"{prop}-light: {value};" for prop, value in values.items()), END]
    return "\n".join(indent + line for line in lines)


def render(scss: str, current: str) -> str:
    """Return `current` with its generated region replaced by one rendered from `scss`."""
    if (region := REGION_RE.search(current)) is None:
        msg = f"{TARGET} has no “{BEGIN}” … “{END}” region"
        raise LookupError(msg)
    return current[: region.start()] + render_region(scss, region[1]) + current[region.end() :]


def main() -> int:
    """Write the refreshed token stylesheet to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--website", type=Path, required=True, help="checkout of scverse/scverse.github.io")
    parser.add_argument("--check", action="store_true", help="fail instead of writing if the output would change")
    args = parser.parse_args()

    scss = (args.website / "assets" / "main.scss").read_text()
    if stale := check_literals(scss):
        print(f"literal brand colours no longer found in main.scss: {', '.join(stale)}", file=sys.stderr)
        return 1

    updates = {
        TARGET: render(scss, TARGET.read_text()).encode(),
        **{dst: (args.website / src).read_bytes() for src, dst in ASSETS.items()},
    }
    if args.check:
        if outdated := [str(dst) for dst, new in updates.items() if not dst.is_file() or dst.read_bytes() != new]:
            print(f"{', '.join(outdated)} out of date; rerun scripts/sync_brand_tokens.py", file=sys.stderr)
            return 1
        return 0
    for dst, new in updates.items():
        dst.write_bytes(new)
        print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
