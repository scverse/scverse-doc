# SPDX-License-Identifier: MPL-2.0
"""The layout of the API pages.

Ships :mod:`~sphinx.ext.autosummary` templates for modules and classes.
A class page gets tables of its attributes and methods, then their documentation,
with each attribute documented as a property, method or plain attribute as appropriate.
Templates of the same name in your own `templates_path` still win.

Also hides ``object``, :class:`~typing.Generic` and private classes from the bases
that ``:show-inheritance:`` lists.
"""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Generic, Literal, get_origin

from jinja2.defaults import DEFAULT_FILTERS  # type: ignore[attr-defined]
from sphinx.ext.autodoc import import_object
from sphinx.util import logging
from sphinx.util.typing import ExtensionMetadata

if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx
    from sphinx.config import Config

__all__ = ["setup"]

_logger = logging.getLogger(__name__)

TEMPLATES = Path(__file__).parent / "templates"


def _member_type(obj_path: str) -> Literal["method", "property", "attribute"]:
    """Determine what kind of member `obj_path` is, for ``.. auto{{ fullname | member_type }}::``."""
    cls_path, cls_name, member_name = obj_path.rsplit(".", 2)
    try:
        cls = import_object(cls_path, [cls_name], "class")[-1]
    except ImportError:
        _logger.error(f"Failed to import {cls_name} from {cls_path}: {traceback.format_exc()}")
        return "attribute"
    match getattr(cls, member_name, None):
        case property():
            return "property"
        case member if callable(member):
            return "method"
        case _:
            return "attribute"


def _skip_private_bases(app: Sphinx, name: str, obj: type, options: Any, bases: list[type | str]) -> None:
    # Other handlers may have added strings, and some typing constructs have no `__name__`.
    bases[:] = [
        b
        for b in bases
        if b is not object
        and get_origin(b) is not Generic
        and not (b if isinstance(b, str) else getattr(b, "__name__", "")).rpartition(".")[2].startswith("_")
    ]


def _add_templates(app: Sphinx, config: Config) -> None:
    # Appended, so the package’s own templates win.
    config.templates_path = [*config.templates_path, str(TEMPLATES)]


def setup(app: Sphinx) -> ExtensionMetadata:
    """Register the templates, their filter, and the bases hook."""
    app.setup_extension("sphinx.ext.autodoc")
    app.setup_extension("sphinx.ext.autosummary")
    # TODO: autosummary builds its own jinja environment with no hook for filters, so this is global.
    DEFAULT_FILTERS["member_type"] = _member_type
    app.connect("config-inited", _add_templates)
    app.connect(
        "autodoc-process-bases", _skip_private_bases, priority=100
    )  # this needs to run before sphinx-autodoc-typehints
    return ExtensionMetadata(parallel_read_safe=True)
