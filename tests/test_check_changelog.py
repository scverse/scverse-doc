# SPDX-License-Identifier: MPL-2.0
"""The PR changelog check in ``scripts/check_changelog.py``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from check_changelog import Changelog, ChangelogError, Entry

if TYPE_CHECKING:
    from pathlib import Path

CHANGELOG = """\
## [Unreleased]

### Fixed

- A `fix` (#1)
- No PR number

## [0.1.0]

### Added

- Old (#3)

[Unreleased]: https://github.com/scverse/scverse-doc/compare/v0.1.0...main
[0.1.0]: https://github.com/scverse/scverse-doc/releases/tag/v0.1.0
"""


def parse(tmp_path: Path, text: str = CHANGELOG) -> Changelog:
    path = tmp_path / "CHANGELOG.md"
    path.write_text(text)
    return Changelog.parse(path)


def test_parse(tmp_path: Path) -> None:
    assert parse(tmp_path).versions == {
        "Unreleased": {"Fixed": [Entry(5, 1), Entry(6, None)]},
        "0.1.0": {"Added": [Entry(12, 3)]},
    }


@pytest.mark.parametrize(
    ("text", "line", "msg"),
    [
        pytest.param(
            CHANGELOG.replace("[Unreleased]", "[0.2.0]"),
            None,
            "No “## [Unreleased]” section",
            id="no-unreleased",
        ),
        pytest.param(
            CHANGELOG.replace("[0.1.0]: ", "[0.1.1]: "),
            8,
            "“## [0.1.0]” isn’t a link; add a “[<version>]: <url>” definition",
            id="heading-without-definition",
        ),
        pytest.param(
            CHANGELOG.replace("No PR number", "(#2)"),
            6,
            "Entry “(#2)” has no description",
            id="placeholder",
        ),
    ],
)
def test_parse_error(tmp_path: Path, text: str, line: int | None, msg: str) -> None:
    with pytest.raises(ChangelogError) as exc_info:
        parse(tmp_path, text)
    assert (exc_info.value.line, exc_info.value.msg) == (line, msg)


@pytest.mark.parametrize(
    ("pr", "title"),
    [
        pytest.param(1, "fix(x)!: y", id="scope-and-breaking"),
        pytest.param(1, "ci: y", id="unchecked-type"),
        pytest.param(4, "docs: y", id="unchecked-type-no-entry"),
    ],
)
def test_check_ok(tmp_path: Path, pr: int, title: str) -> None:
    parse(tmp_path).check(pr, title)


@pytest.mark.parametrize(
    ("pr", "title", "line", "msg"),
    [
        pytest.param(
            1,
            "feat: y",
            5,
            "Entry for #1 is under “## [Unreleased]” › “### Fixed”, but “feat: y” needs “## [Unreleased]” › “### Added”",
            id="wrong-section",
        ),
        pytest.param(
            3,
            "feat: y",
            12,
            "Entry for #3 is under “## [0.1.0]” › “### Added”, but “feat: y” needs “## [Unreleased]” › “### Added”",
            id="wrong-release",
        ),
        pytest.param(
            4,
            "fix: y",
            None,
            "No list item ending in “(#4)”; “fix: y” needs one under “## [Unreleased]” › “### Fixed”",
            id="missing",
        ),
    ],
)
def test_check_error(tmp_path: Path, pr: int, title: str, line: int | None, msg: str) -> None:
    with pytest.raises(ChangelogError) as exc_info:
        parse(tmp_path).check(pr, title)
    assert (exc_info.value.line, exc_info.value.msg) == (line, msg)


def test_error_exits_with_annotation(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc_info:
        parse(tmp_path).check(4, "fix: y")
    assert str(exc_info.value.code).startswith(f"::error file={tmp_path / 'CHANGELOG.md'}::No list item")
