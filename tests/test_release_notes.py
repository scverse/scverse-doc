# SPDX-License-Identifier: MPL-2.0
"""The ``release-notes`` directive."""

from __future__ import annotations

import re
from importlib.util import find_spec
from textwrap import dedent
from typing import TYPE_CHECKING, Literal

import pytest
from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from pathlib import Path

type Format = Literal["rst", "myst"]

FILES: dict[Format, dict[str, str]] = {
    "rst": {
        "1.2.0.rst": ".. _v1.2.0:\n1.2.0\n=====",
        "1.2.1.rst": ".. _v1.2.1:\n1.2.1\n=====",
        "1.3.0rc1.rst": ".. _v1.3.0rc1:\n1.3.0rc1\n========",
    },
    "myst": {
        "1.2.0.md": "(v1.2.0)=\n### 1.2.0",
        "1.2.1.md": "(v1.2.1)=\n### 1.2.1",
        "1.3.0rc1.md": "(v1.3.0rc1)=\n### 1.3.0rc1",
    },
}

EXPECTED = """\
<target refid="v1-3">
<section ids="version-1-3 v1-3" names="version\\ 1.3 v1.3">
    <title>
        Version 1.3
    <target refid="v1-3-0rc1">
    <section ids="rc1 v1-3-0rc1" names="1.3.0rc1 v1.3.0rc1">
        <title>
            1.3.0rc1
<target refid="v1-2">
<section ids="version-1-2 v1-2" names="version\\ 1.2 v1.2">
    <title>
        Version 1.2
    <target refid="v1-2-1">
    <section ids="v1-2-1 id1" names="1.2.1 v1.2.1">
        <title>
            1.2.1
    <target refid="v1-2-0">
    <section ids="v1-2-0 id2" names="1.2.0 v1.2.0">
        <title>
            1.2.0
"""


@pytest.fixture(
    params=[
        "rst",
        pytest.param("myst", marks=pytest.mark.skipif(find_spec("myst_parser") is None, reason="needs myst-parser")),
    ]
)
def file_format(request: pytest.FixtureRequest) -> Format:
    return request.param  # type: ignore[no-any-return]


def build(tmp_path: Path, file_format: Format, arg: str, files: dict[str, str]) -> tuple[Path, str]:
    """Write `files` and an index calling the directive with `arg` to `tmp_path`, build it, and return the output dir and warnings."""
    index = f"```{{release-notes}} {arg}\n```" if file_format == "myst" else f".. release-notes:: {arg}"
    files = {f"index.{'md' if file_format == 'myst' else 'rst'}": index, **files}
    for name, content in files.items():
        (tmp_path / name).write_text(content)
    (tmp_path / "conf.py").write_text("")
    app = SphinxTestApp(
        "pseudoxml",
        srcdir=tmp_path,
        confoverrides={
            "extensions": [*(["myst_parser"] if file_format == "myst" else []), "scverse_doc.release_notes"],
            # the version files are only included
            "exclude_patterns": ["_build", "[!i]*.md", "[!i]*.rst"],
        },
    )
    try:
        app.build()
    finally:
        app.cleanup()
    return app.outdir, app.warning.getvalue()


def test_release_notes(tmp_path: Path, file_format: Format) -> None:
    out, _ = build(tmp_path, file_format, ".", FILES[file_format])
    index_out = (out / "index.pseudoxml").read_text()
    assert "\n".join(l[4:] for l in dedent(index_out).splitlines()[1:]) == EXPECTED.strip()


@pytest.mark.parametrize(
    ("arg", "files"),
    [
        pytest.param("doesnt-exist.txt", {}, id="nothing"),
        pytest.param("file.txt", {"file.txt": "cont"}, id="file"),
    ],
)
def test_error_not_a_dir(tmp_path: Path, file_format: Format, arg: str, files: dict[str, str]) -> None:
    _, warnings = build(tmp_path, file_format, arg, files)
    assert re.search(rf"Not a directory:.*{re.escape(arg)}", warnings)
