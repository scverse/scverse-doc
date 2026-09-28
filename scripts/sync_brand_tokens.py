#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Refresh the generated brand assets from the scverse website.

The website is the brand’s source of truth,
so transcribing its colours into this repository by hand
would create exactly the kind of drift this package exists to remove.

The website takes its neutral colours from Bootstrap’s tokens (``--bs-fg-*``, ``--bs-bg-*``, …),
which already carry dark values via ``light-dark()``, and defines only the brand hues itself.
This script looks up the tokens the theme needs in the website’s vendored Bootstrap and ``assets/main.scss``,
resolves every ``var()`` down to literals, and writes them into ``_tokens.css`` as ``--scverse-color-x``.

Only the region between the marker comments is touched; the rest of the file is hand-authored.

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

#: CSS custom property emitted here -> website custom property it is resolved from.
#: The pairing mirrors the one scverse/scverse.github.io#329 used when replacing its SCSS variables.
TOKEN_MAP = {
    "--scverse-color-gradient-start": "--scverse-deep-blue",
    "--scverse-color-gradient-end": "--scverse-sky-blue",
    "--scverse-color-background": "--bs-bg-body",
    "--scverse-color-text": "--bs-fg-body",
    "--scverse-color-heading": "--bs-fg-1",
    "--scverse-color-text-secondary": "--bs-fg-2",
    "--scverse-color-text-muted": "--bs-fg-3",
    "--scverse-color-surface": "--bs-bg-2",
    "--scverse-color-surface-alt": "--bs-bg-1",
    "--scverse-color-border": "--bs-border-color",
    "--scverse-color-border-muted": "--bs-border-muted",
    "--scverse-color-code-bg": "--bs-bg-1",
    "--scverse-color-code-text": "--bs-fg-1",
    "--scverse-color-footer-bg": "--bs-bg-2",
}

BEGIN = "/* BEGIN GENERATED BRAND TOKENS – DO NOT EDIT; regenerate with scripts/sync_brand_tokens.py */"
END = "/* END GENERATED BRAND TOKENS */"

#: The fenced region, captured together with the indentation of its opening marker.
REGION_RE = re.compile(rf"^([ \t]*){re.escape(BEGIN)}\n.*?^[ \t]*{re.escape(END)}$", re.DOTALL | re.MULTILINE)
DECL_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;{}]+?)\s*;")


def parse_bootstrap(css: str) -> dict[str, str]:
    """Extract the custom properties Bootstrap declares on ``:root``."""
    blocks = re.findall(r":root,:host\{([^}]*)\}", css)
    return dict(DECL_RE.findall(";".join(blocks) + ";"))


def parse_scss(scss: str) -> dict[str, str]:
    """Extract custom property declarations from the website’s SCSS."""
    return dict(DECL_RE.findall(scss))


def resolve(name: str, props: dict[str, str]) -> str:
    """Return the value of `name` with every ``var()`` in it recursively substituted."""
    return re.sub(r"var\((--[\w-]+)\)", lambda m: resolve(m[1], props), props[name])


def render_region(props: dict[str, str], indent: str) -> str:
    """Render the generated region – marker comments included – indented by `indent`."""
    if missing := sorted(set(TOKEN_MAP.values()) - set(props)):
        msg = f"custom properties vanished from the website: {', '.join(missing)}"
        raise KeyError(msg)
    lines = [BEGIN, *(f"{prop}: {resolve(src, props)};" for prop, src in TOKEN_MAP.items()), END]
    return "\n".join(indent + line for line in lines)


def render(props: dict[str, str], current: str) -> str:
    """Return `current` with its generated region replaced by one rendered from `props`."""
    if (region := REGION_RE.search(current)) is None:
        msg = f"{TARGET} has no “{BEGIN}” … “{END}” region"
        raise LookupError(msg)
    return current[: region.start()] + render_region(props, region[1]) + current[region.end() :]


def main() -> int:
    """Write the refreshed token stylesheet to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--website", type=Path, required=True, help="checkout of scverse/scverse.github.io")
    parser.add_argument("--check", action="store_true", help="fail instead of writing if the output would change")
    args = parser.parse_args()

    props = parse_bootstrap(
        (args.website / "static" / "bootstrap" / "css" / "bootstrap.min.css").read_text()
    ) | parse_scss((args.website / "assets" / "main.scss").read_text())
    updates = {
        TARGET: render(props, TARGET.read_text()).encode(),
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
