# SPDX-License-Identifier: MPL-2.0
"""The autodoc and napoleon tweaks."""

from __future__ import annotations

import pytest
from sphinx.ext.napoleon import Config, NumpyDocstring

from scverse_doc import napoleon
from scverse_doc.autodoc import _member_type, _skip_private_bases


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        pytest.param("collections.OrderedDict.keys", "method", id="method"),
        pytest.param("scverse_doc.registry.Package.name", "attribute", id="attribute"),
        pytest.param("not_a_module.Cls.x", "attribute", id="unimportable"),
    ],
)
def test_member_type(path: str, expected: str) -> None:
    assert _member_type(path) == expected


def test_skip_private_bases() -> None:
    class _Private: ...

    bases: list[type | str] = [object, _Private, dict, ":class:`~pkg._Hidden`", ":class:`pkg.Public`"]
    _skip_private_bases(None, "x", object, None, bases)  # type: ignore[arg-type]
    assert bases == [dict, ":class:`pkg.Public`"]


@pytest.mark.parametrize(
    ("doc", "expected"),
    [
        pytest.param("Returns\n-------\n:\n    The thing.\n", ":returns:     The thing.\n", id="colon"),
        pytest.param("Returns\n-------\nx : int\n", ":returns: -x (:class:`~int`)\n", id="typed"),
        pytest.param(
            "Returns\n-------\nThe thing.\n\nNotes\n-----\nhi\n",
            ":returns: The thing.\n\n.. rubric:: Notes\n\nhi\n",
            id="followed",
        ),
    ],
)
def test_returns_section(monkeypatch: pytest.MonkeyPatch, doc: str, expected: str) -> None:
    monkeypatch.setattr(NumpyDocstring, "_parse_returns_section", napoleon._parse_returns_section)
    assert str(NumpyDocstring(doc, Config())) == expected  # type: ignore[arg-type]


def test_unresolvable_hints_annotate_nothing() -> None:
    assert list(napoleon._return_tuples(1)) == []
