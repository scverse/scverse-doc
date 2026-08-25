"""The branch edit links point at."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from scverse_doc.theme import _branch

if TYPE_CHECKING:
    from collections.abc import Mapping


@pytest.fixture(autouse=True)
def _no_rtd(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("READTHEDOCS_GIT_IDENTIFIER", "READTHEDOCS_VERSION_TYPE"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        pytest.param({}, "main", id="local"),
        pytest.param({"READTHEDOCS_GIT_IDENTIFIER": "1.2.x"}, "1.2.x", id="rtd-branch"),
        pytest.param({"READTHEDOCS_GIT_IDENTIFIER": "42", "READTHEDOCS_VERSION_TYPE": "external"}, "main", id="rtd-pr"),
    ],
)
def test_derives_branch(monkeypatch: pytest.MonkeyPatch, env: Mapping[str, str], expected: str) -> None:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    assert _branch({}) == expected


def test_option_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("READTHEDOCS_GIT_IDENTIFIER", "1.2.x")
    assert _branch({"branch": "master"}) == "master"
