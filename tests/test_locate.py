# SPDX-License-Identifier: MPL-2.0
"""Finding where Python objects are defined, including where :mod:`inspect` can’t."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

import scverse_doc
from scverse_doc.source import _forge
from scverse_doc.source._locate import Location, locate

SNIPPETS = '''\
import typing

type Alias = (
    int | str
)
Called = typing.TypeAliasType("Called", int)


class Holder:
    plain = 1
    annotated: int = 2
    """Docstring."""

    @property
    def prop(self) -> int:
        return 1

    @prop.setter
    def prop(self, value: int) -> None: ...


class Fields(typing.NamedTuple):
    x: int
'''


@pytest.fixture
def snippets(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Importable module ``snippets`` with objects :mod:`inspect` can’t locate."""
    (file := tmp_path / "snippets.py").write_text(SNIPPETS)
    monkeypatch.syspath_prepend(tmp_path)
    monkeypatch.delitem(sys.modules, "snippets", raising=False)
    return file


@pytest.mark.parametrize(
    ("fullname", "span"),
    [
        pytest.param("Alias", (3, 5), id="type-alias"),
        pytest.param("Holder.plain", (10, 10), id="attribute"),
        pytest.param("Holder.annotated", (11, 12), id="attribute-docstring"),
        pytest.param("Holder.prop", (14, 19), id="property-setter"),
        pytest.param("Fields.x", (23, 23), id="namedtuple-field"),
    ],
)
def test_spans(snippets: Path, fullname: str, span: tuple[int, int]) -> None:
    assert locate("snippets", fullname) == Location(snippets, span)


def test_module_is_its_whole_file(snippets: Path) -> None:
    assert locate("snippets", "") == Location(snippets, None)


@pytest.mark.parametrize(
    ("module", "fullname"),
    [
        pytest.param("scverse_doc.source._forge", "Source.icon_link", id="property"),
        pytest.param("scverse_doc.registry", "_RegistryInventories._resolved", id="cached_property"),
    ],
)
def test_finds_descriptors(module: str, fullname: str) -> None:
    location = locate(module, fullname)
    assert location is not None
    assert location.file == Path(inspect.getsourcefile(sys.modules[module]) or "")
    assert location.span is not None


def test_sees_through_reexported_class(monkeypatch: pytest.MonkeyPatch) -> None:
    """Like ``AnnData.__module__ = "anndata"``."""
    _, start = inspect.getsourcelines(_forge.Source)
    monkeypatch.setattr(_forge.Source, "__module__", "scverse_doc")
    monkeypatch.setattr(scverse_doc, "Source", _forge.Source, raising=False)
    location = locate("scverse_doc", "Source")
    assert location is not None
    assert location.file == Path(_forge.__file__)
    assert location.span is not None
    assert location.span[0] == start


@pytest.mark.usefixtures("snippets")
@pytest.mark.parametrize(
    ("module", "fullname"),
    [
        pytest.param("scverse_doc.registry", "nope", id="missing"),
        pytest.param("scverse_doc.config", "DEFAULTS", id="no-source-lines"),
        pytest.param("snippets", "Called", id="no-type-statement"),
        pytest.param("snippets", "Fields._fields", id="not-in-class-body"),
    ],
)
def test_gives_up_quietly(module: str, fullname: str) -> None:
    assert locate(module, fullname) is None
