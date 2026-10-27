#!/usr/bin/env -S uv run --script
# SPDX-License-Identifier: MPL-2.0
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Refresh the files generated or copied from upstream: the scverse website and math-core.

The website is the brand’s source of truth,
so transcribing its colours into this repository by hand
would create exactly the kind of drift this package exists to remove.

The website takes its neutral colours from Bootstrap’s tokens (``--bs-fg-*``, ``--bs-bg-*``, …),
which already carry dark values via ``light-dark()``, and defines only the brand hues itself,
as OKLCH triples in ``assets/accents.json``.
This script looks up the tokens the theme needs in the website’s vendored Bootstrap and ``accents.json``,
resolves every ``var()`` down to literals, and writes them into ``_tokens.css`` as ``--scverse-color-x``.
Only the region between the marker comments is touched; the rest of the file is hand-authored.

The scverse logo used for the navbar link back to the website is copied verbatim for the same reason,
as is ``accents.json``, which the registry reads the package accents from.

math-core’s stylesheet fixing browsers’ MathML rendering is copied verbatim from its repository.

Usage
-----
    uv run scripts/sync_upstream.py --website ../scverse.github.io --math-core ../math-core
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
STATIC = HERE.parent / "src" / "scverse_doc" / "theme" / "scverse" / "static"
TARGET = STATIC / "styles" / "_tokens.css"

#: Website file -> package file, copied verbatim.
ASSETS = {
    Path("static/img/logo/scverse-fa.svg"): STATIC / "scverse-fa.svg",
    Path("assets/accents.json"): HERE.parent / "src" / "scverse_doc" / "_accents.json",
}

#: math-core file -> package file, copied verbatim.
MATH_CORE_ASSETS = {
    Path("css/mathmlfixes.css"): HERE.parent / "src" / "scverse_doc" / "static" / "mathmlfixes.css",
}

#: CSS custom property emitted here -> website custom property it is resolved from.
#: The pairing mirrors the one scverse/scverse.github.io#329 used when replacing its SCSS variables.
TOKEN_MAP = {
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

#: CSS custom property emitted here -> (package, colour name) in the website’s ``accents.json``.
ACCENT_TOKEN_MAP = {
    "--scverse-color-gradient-start": ("scverse", "deep-blue"),
    "--scverse-color-gradient-end": ("scverse", "sky-blue"),
}

BEGIN = "/* BEGIN GENERATED BRAND TOKENS – DO NOT EDIT; regenerate with scripts/sync_upstream.py */"
END = "/* END GENERATED BRAND TOKENS */"

#: The fenced region, captured together with the indentation of its opening marker.
REGION_RE = re.compile(rf"^([ \t]*){re.escape(BEGIN)}\n.*?^[ \t]*{re.escape(END)}$", re.DOTALL | re.MULTILINE)
DECL_RE = re.compile(r"(--[\w-]+)\s*:\s*([^;{}]+?)\s*;")


def parse_bootstrap(css: str) -> dict[str, str]:
    """Extract the custom properties Bootstrap declares on ``:root``."""
    blocks = re.findall(r":root,:host\{([^}]*)\}", css)
    return dict(DECL_RE.findall(";".join(blocks) + ";"))


def resolve(name: str, props: dict[str, str]) -> str:
    """Return the value of `name` with every ``var()`` in it recursively substituted."""
    return re.sub(r"var\((--[\w-]+)\)", lambda m: resolve(m[1], props), props[name])


def render_region(props: dict[str, str], accents: dict[str, list[tuple[str, list[float]]]], indent: str) -> str:
    """Render the generated region – marker comments included – indented by `indent`."""
    if missing := sorted(set(TOKEN_MAP.values()) - set(props)):
        msg = f"custom properties vanished from the website: {', '.join(missing)}"
        raise KeyError(msg)
    lines = [
        BEGIN,
        *(
            f"{prop}: oklch({' '.join(map(str, dict(accents[pkg])[name]))});"
            for prop, (pkg, name) in ACCENT_TOKEN_MAP.items()
        ),
        *(f"{prop}: {resolve(src, props)};" for prop, src in TOKEN_MAP.items()),
        END,
    ]
    return "\n".join(indent + line for line in lines)


def render(props: dict[str, str], accents: dict[str, list[tuple[str, list[float]]]], current: str) -> str:
    """Return `current` with its generated region replaced by one rendered from `props` and `accents`."""
    if (region := REGION_RE.search(current)) is None:
        msg = f"{TARGET} has no “{BEGIN}” … “{END}” region"
        raise LookupError(msg)
    return current[: region.start()] + render_region(props, accents, region[1]) + current[region.end() :]


def main() -> int:
    """Write the refreshed token stylesheet to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--website", type=Path, required=True, help="checkout of scverse/scverse.github.io")
    parser.add_argument("--math-core", type=Path, required=True, help="checkout of tmke8/math-core")
    parser.add_argument("--check", action="store_true", help="fail instead of writing if the output would change")
    args = parser.parse_args()

    props = parse_bootstrap((args.website / "static" / "bootstrap" / "css" / "bootstrap.min.css").read_text())
    accents = json.loads((args.website / "assets" / "accents.json").read_text())
    updates = {
        TARGET: render(props, accents, TARGET.read_text()).encode(),
        **{dst: (args.website / src).read_bytes() for src, dst in ASSETS.items()},
        **{dst: (args.math_core / src).read_bytes() for src, dst in MATH_CORE_ASSETS.items()},
    }
    if args.check:
        if outdated := [str(dst) for dst, new in updates.items() if not dst.is_file() or dst.read_bytes() != new]:
            print(f"{', '.join(outdated)} out of date; rerun scripts/sync_upstream.py", file=sys.stderr)
            return 1
        return 0
    for dst, new in updates.items():
        dst.write_bytes(new)
        print(f"wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
