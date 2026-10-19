# SPDX-License-Identifier: MPL-2.0
"""Parameters and attributes as definition lists.

Sphinx renders typed fields (``:param:`` with ``:type:``, ``:var:`` with ``:vartype:``, …)
as a list of paragraphs, cramming name, type, and description into one line.
This extension renders them as definition lists instead, like numpydoc:

.. code:: rst

   .. py:function:: test(a)

      :param a: Only parameter
      :type a: str

renders the term ``a`` classified as :class:`str`, with the description indented below it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from docutils import nodes
from sphinx import addnodes
from sphinx.domains.python import PyObject, PyTypedField
from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment

    type TextLikeNode = nodes.Text | nodes.TextElement

__all__ = ["setup"]


class _DLTypedField(PyTypedField):
    """A :class:`~sphinx.domains.python.PyTypedField` that renders its items as a definition list."""

    list_type: ClassVar = nodes.definition_list  # type: ignore[misc,assignment]

    def make_field(  # type: ignore[override]
        self,
        types: dict[str, list[nodes.Node]],
        domain: str,
        items: Iterable[tuple[str, list[nodes.inline]]],
        env: BuildEnvironment | None = None,
        **kw: Any,
    ) -> nodes.field:
        """Render a field to a node holding a definition list."""

        def make_refs(role_name: str, name: str, node: type[TextLikeNode]) -> list[nodes.Node]:
            return self.make_xrefs(role_name, domain, name, node, env=env, **kw)

        def handle_item(fieldarg: str, content: list[nodes.inline]) -> nodes.definition_list_item:
            term = nodes.term()
            term += make_refs(self.rolename, fieldarg, addnodes.literal_strong)

            field_type = types.pop(fieldarg, None)
            if field_type is not None:
                # convert `param : SomeClass` into reference
                if len(field_type) == 1 and isinstance(field_type[0], nodes.Text):
                    classifier_content = make_refs(self.typerolename, field_type[0].astext(), addnodes.literal_emphasis)
                else:
                    classifier_content = field_type
                term += [
                    # https://github.com/sphinx-doc/sphinx/issues/10815
                    nodes.Text(" "),
                    # Sphinx tries to fixup classifiers without rawsource,
                    # but for this expects attributes we don’t have. Thus “×”.
                    nodes.classifier("×", "", *classifier_content),
                ]

            definition = nodes.definition("", nodes.paragraph("", "", *content))
            return nodes.definition_list_item("", term, definition)

        assert not self.can_collapse
        body_node = self.list_type(classes=["simple"])
        for field_arg, content in items:
            body_node += handle_item(field_arg, content)
        return nodes.field("", nodes.field_name("", self.label), nodes.field_body("", body_node))


def _replace_fields(app: Sphinx) -> None:
    PyObject.doc_field_types = [
        _DLTypedField(
            ft.name,
            names=ft.names,
            typenames=ft.typenames,
            label=ft.label,
            rolename=ft.rolename,
            typerolename=ft.typerolename,
            # Definition lists can’t collapse.
            can_collapse=False,
        )
        if isinstance(ft, PyTypedField)
        else ft
        for ft in PyObject.doc_field_types
    ]


def setup(app: Sphinx) -> ExtensionMetadata:
    """Replace the Python domain’s :class:`~sphinx.domains.python.PyTypedField` fields with definition list ones."""
    # After every extension’s setup, so napoleon’s `keyword` field is replaced too.
    app.connect("builder-inited", _replace_fields)
    return ExtensionMetadata(parallel_read_safe=True)
