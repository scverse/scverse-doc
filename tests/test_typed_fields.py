# SPDX-License-Identifier: MPL-2.0
"""Typed fields as definition lists."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes
from sphinx import addnodes
from sphinx.domains.python import PyObject
from sphinx.testing.restructuredtext import parse
from sphinx.testing.util import SphinxTestApp, assert_node

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

# Avoid :class: to not get pending_xref. TODO: fix
PARAMS_SINGLE = """\
.. py:function:: test(a)

   :param a: Only parameter
   :type a: ``str``
"""

PARAMS = """\
.. py:function:: test(a, b=None)

   :param a: First parameter
   :type a: str
   :param b: Second parameter
   :type b: ``~typing.Optional``\\[``str``]
"""


@pytest.fixture(autouse=True)
def _restore_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Undo the extension’s (and napoleon’s) global patch after each test."""
    monkeypatch.setattr(PyObject, "doc_field_types", list(PyObject.doc_field_types))


def make_app(tmp_path: Path, *extensions: str) -> SphinxTestApp:
    (tmp_path / "conf.py").write_text("")
    return SphinxTestApp("html", srcdir=tmp_path, confoverrides={"extensions": list(extensions)})


@pytest.fixture
def app(tmp_path: Path) -> Iterator[SphinxTestApp]:
    app = make_app(tmp_path, "scverse_doc.typed_fields")
    yield app
    app.cleanup()


@pytest.mark.parametrize(
    ("code", "classifiers"),
    [
        pytest.param(PARAMS_SINGLE, [nodes.literal], id="single"),
        pytest.param(
            PARAMS,
            [
                addnodes.pending_xref,  # a plain type becomes a reference
                (nodes.literal, nodes.Text, nodes.literal, nodes.Text),  # markup stays as is
            ],
            id="multi",
        ),
    ],
)
def test_convert_params(app: SphinxTestApp, code: str, classifiers: list[object]) -> None:
    # each parameter is a dl item: a term with name, spacer and type, and a definition
    items = tuple(
        [
            nodes.definition_list_item,
            ([nodes.term, (addnodes.literal_strong, " ", [nodes.classifier, cls])], nodes.definition),
        ]
        for cls in classifiers
    )
    fields = [
        addnodes.desc_content,
        nodes.field_list,
        nodes.field,
        ([nodes.field_name, "Parameters"], [nodes.field_body, nodes.definition_list, items]),
    ]
    desc = parse(app, code)[1]
    assert_node(desc, addnodes.desc, desctype="function")
    assert_node(desc, [addnodes.desc, (addnodes.desc_signature, fields)])


def test_napoleon_after(tmp_path: Path) -> None:
    """Napoleon’s `keyword` field is replaced even when napoleon is loaded later."""
    app = make_app(tmp_path, "scverse_doc.typed_fields", "sphinx.ext.napoleon")
    try:
        # napoleon appends one per setup, so earlier apps in this process leave more
        keywords = [ft for ft in PyObject.doc_field_types if ft.name == "keyword"]
        assert keywords
        assert all(type(ft).__name__ == "_DLTypedField" for ft in keywords)
    finally:
        app.cleanup()
