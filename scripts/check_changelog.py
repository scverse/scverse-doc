#!/usr/bin/env -S uv run --script
# SPDX-License-Identifier: MPL-2.0
# /// script
# requires-python = ">=3.12"
# dependencies = ["wenmode"]
# ///
"""Check that a PR’s changelog entry is in the section its conventional-commit title implies.

The entry is a list item under `## [Unreleased]` › `### <Section>` that ends with the PR number,
e.g. `- Some fix (#67)`.
PR titles with types that don’t map to a section (`ci:`, `docs:`, …) pass unchecked.

Usage
-----
    uv run scripts/check_changelog.py --pr 67 --title 'fix: make logo fill sidebar'
"""

from __future__ import annotations

import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

from wenmode import Wenmode
from wenmode.nodes import Heading, List, ListItem, Literal, Paragraph, Text

if TYPE_CHECKING:
    from collections.abc import Generator

SECTIONS = {"feat": "Added", "fix": "Fixed", "perf": "Changed"}


def find_entries(changelog: str, pr: int) -> Generator[tuple[int, str | None, str | None]]:
    """Find list items ending in `(#<pr>)` as `(line, h2, h3)`."""
    suffix = f"(#{pr})"
    h2: str | None = None
    h3: str | None = None
    for node in Wenmode(positions=True).parse(changelog).children:
        match node:
            case Heading(depth=2 | 3 as depth, children=children):
                text = "".join(c.value for c in children if isinstance(c, Literal))
                h2, h3 = (text, None) if depth == 2 else (h2, text)
            case List(children=items):
                for item in items:
                    match item:
                        case ListItem(children=[Paragraph(children=[*rest, Text(value=value)]), *_]):
                            # an item consisting only of the PR number is a placeholder, not an entry
                            if value.endswith(suffix) and (rest or value != suffix):
                                assert item.position is not None
                                yield (changelog.count("\n", 0, item.position.start) + 1, h2, h3)


def check(changelog: str, pr: int, title: str) -> tuple[int | None, str] | None:
    """Return `(line, message)` describing the problem, or `None` if the entry is fine."""
    if not (m := re.match(r"(\w+)(?:\([^)]*\))?!?:", title)) or not (want := SECTIONS.get(m[1])):
        return None
    entries = list(find_entries(changelog, pr))
    if any(h2 == "[Unreleased]" and h3 == want for _, h2, h3 in entries):
        return None
    if not entries:
        return None, f"No list item ending in “(#{pr})”; “{title}” needs one under “## [Unreleased]” › “### {want}”"
    line, h2, h3 = entries[0]
    return (
        line,
        f"Entry for #{pr} is under “## {h2}” › “### {h3}”, but “{title}” needs “## [Unreleased]” › “### {want}”",
    )


def main() -> int:
    """Return 0 if the entry is in the right section, else print a GitHub annotation and return 1."""
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    args = parser.parse_args()

    _self_check()
    if (problem := check(args.changelog.read_text(), args.pr, args.title)) is None:
        return 0
    line, msg = problem
    loc = f"file={args.changelog}{f',line={line}' if line else ''}"
    print(f"::error {loc}::{msg}")
    return 1


def _self_check() -> None:
    cl = "## [Unreleased]\n\n### Fixed\n\n- A `fix` (#1)\n- (#2)\n\n## [0.1.0]\n\n### Added\n\n- Old (#3)\n"
    assert check(cl, 1, "fix(x)!: y") is None
    assert check(cl, 1, "ci: y") is None
    assert check(cl, 1, "feat: y") == (5, "Entry for #1 is under “## [Unreleased]” › “### Fixed”, but “feat: y” needs “## [Unreleased]” › “### Added”")  # fmt: skip
    assert check(cl, 2, "fix: y") is not None  # placeholder
    assert (r := check(cl, 3, "feat: y")) is not None and r[0] == 12  # wrong release
    assert check(cl, 4, "fix: y") is not None


if __name__ == "__main__":
    sys.exit(main())
