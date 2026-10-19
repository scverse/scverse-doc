# SPDX-License-Identifier: MPL-2.0
"""Prose return sections in NumPy-style docstrings.

:mod:`sphinx.ext.napoleon` reads a NumPy-style ``Returns`` section as a list of ``name : type`` entries.
With this extension, it can be prose instead:

.. code:: rst

   Returns
   -------
   The fitted model, or `None` if `copy` is false.

Lines that do look like ``name : type`` become an item linking to `type`.

If the section is a single definition list with *n* items,
and the return type is a tuple with *n* members (or a union with such a tuple),
each item is annotated with its member type,
e.g. for a function annotated ``-> tuple[AnnData, AnnData]``:

.. code:: rst

   Returns
   -------
   train
       The training set.
   test
       The test set.
"""

from __future__ import annotations

import re
from types import UnionType
from typing import TYPE_CHECKING, Union, get_args, get_origin, get_type_hints

from sphinx.ext.napoleon import NumpyDocstring  # type: ignore[attr-defined]
from sphinx.util.typing import ExtensionMetadata, restify

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from sphinx.application import Sphinx

__all__ = ["setup"]


def _process_return(lines: Iterable[str]) -> Iterator[str]:
    for line in lines:
        if m := re.fullmatch(r"(?P<param>\w+)\s+:\s+(?P<type>[\w.]+)", line):
            yield f"-{m['param']} (:class:`~{m['type']}`)"
        else:
            yield line


def _return_tuples(obj: object) -> Iterator[tuple[object, ...]]:
    """Yield the member types of each fixed-length tuple `obj` can return."""
    try:
        ret = get_type_hints(obj).get("return")
    except Exception:  # noqa: BLE001  # shortcut: unresolvable hints (e.g. `TYPE_CHECKING` imports) get no types
        return
    for option in get_args(ret) if get_origin(ret) in {Union, UnionType} else [ret]:
        if get_origin(option) is tuple and ... not in (members := get_args(option)):
            yield members


def _annotate_items(lines: list[str], obj: object) -> list[str]:
    """Annotate a definition list’s terms with the members of a returned tuple of the same length."""
    terms = [i for i, line in enumerate(lines) if line and not line[0].isspace()]
    if not all(lines[i].isidentifier() and lines[i + 1 : i + 2] and lines[i + 1][:1].isspace() for i in terms):
        return lines
    for members in _return_tuples(obj):
        if len(members) == len(terms):
            for i, member in zip(terms, members, strict=True):
                lines[i] = f"{lines[i]} : {restify(member, 'smart')}"
            break
    return lines


def _parse_returns_section(self: NumpyDocstring, section: str) -> list[str]:
    lines_raw = self._dedent(self._consume_to_next_section())
    if lines_raw and lines_raw[0] == ":":
        del lines_raw[0]
    lines_raw = _annotate_items(lines_raw, self._obj)
    lines = self._format_block(":returns: ", list(_process_return(lines_raw)))
    if lines and lines[-1]:
        lines.append("")
    return lines


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up napoleon and make it read ``Returns`` sections as prose."""
    app.setup_extension("sphinx.ext.napoleon")
    # TODO: patches private napoleon API; replace once napoleon has a hook for this.
    NumpyDocstring._parse_returns_section = _parse_returns_section  # type: ignore[method-assign,assignment]
    return ExtensionMetadata(parallel_read_safe=True)
