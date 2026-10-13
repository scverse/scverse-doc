"""Prose return sections in NumPy-style docstrings.

:mod:`sphinx.ext.napoleon` reads a NumPy-style ``Returns`` section as a list of ``name : type`` entries.
With this extension, it can be prose instead:

.. code:: rst

   Returns
   -------
   The fitted model, or `None` if `copy` is false.

Lines that do look like ``name : type`` become an item linking to `type`.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sphinx.ext.napoleon import NumpyDocstring  # type: ignore[attr-defined]
from sphinx.util.typing import ExtensionMetadata

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


def _parse_returns_section(self: NumpyDocstring, section: str) -> list[str]:
    lines_raw = self._dedent(self._consume_to_next_section())
    if lines_raw and lines_raw[0] == ":":
        del lines_raw[0]
    lines = self._format_block(":returns: ", list(_process_return(lines_raw)))
    if lines and lines[-1]:
        lines.append("")
    return lines


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up napoleon and make it read ``Returns`` sections as prose."""
    app.setup_extension("sphinx.ext.napoleon")
    # ponytail: patches private napoleon API; replace once napoleon has a hook for this.
    NumpyDocstring._parse_returns_section = _parse_returns_section  # type: ignore[method-assign,assignment]
    return ExtensionMetadata(parallel_read_safe=True)
