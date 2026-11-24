# SPDX-License-Identifier: MPL-2.0
"""Find the file and lines a Python object is defined in, including where :mod:`inspect` can’t."""

from __future__ import annotations

import ast
import inspect
from functools import cached_property
from importlib import import_module
from pathlib import Path
from typing import NamedTuple, TypeAliasType, cast

__all__ = ["Location", "locate"]


class Location(NamedTuple):
    """Where an object is defined."""

    file: Path
    span: tuple[int, int] | None
    """First and last line, or :data:`None` for a whole module."""


def locate(module: str, fullname: str) -> Location | None:
    """Where the object at `fullname` in `module` is defined, or :data:`None` if it has no findable source."""
    try:
        owner: object = None
        obj: object = import_module(module)
        for part in filter(None, fullname.split(".")):
            owner, obj = obj, getattr(obj, part)
        # A property is its getter.
        if isinstance(obj, property):
            obj = obj.fget
        elif isinstance(obj, cached_property):
            obj = obj.func
        obj = cast("object", inspect.unwrap(obj)) if callable(obj) else obj
        if inspect.isclass(owner) and (location := _locate_member(owner, fullname.rpartition(".")[2])):
            return location
        if inspect.isclass(obj) and (found := _class_node(obj)):
            return Location(found[0], _span(found[1]))
        if isinstance(obj, TypeAliasType) and (location := _locate_type_alias(obj)):
            return location
        # Unsupported objects raise `TypeError`, caught below.
        lines, start = inspect.getsourcelines(obj)  # type: ignore[arg-type]
        file = Path(inspect.getsourcefile(obj) or "")  # type: ignore[arg-type]
    except (ImportError, AttributeError, TypeError, OSError):
        return None
    # A module is its whole file.
    return Location(file, None if inspect.ismodule(obj) else (start, start + len(lines) - 1))


def _span(first: ast.stmt, last: ast.stmt | None = None) -> tuple[int, int]:
    """Lines from `first` (with its decorators) to the end of `last` (default: `first`)."""
    start = min([first.lineno, *(d.lineno for d in getattr(first, "decorator_list", ()))])
    return start, (last or first).end_lineno or start


def _class_node(cls: type) -> tuple[Path, ast.ClassDef] | None:
    """File and ``class`` statement of `cls`, preferably found via its methods’ code.

    Packages often set ``__module__`` to the public one (e.g. ``AnnData.__module__ = "anndata"``),
    which makes :mod:`inspect` search the wrong file. Code objects keep the real one.
    """
    methods = (cast("object", inspect.unwrap(m)) for m in vars(cls).values())
    # The code’s own qualname, since e.g. `dataclass` and `namedtuple` set `__qualname__` on generated methods.
    own = (m for m in methods if inspect.isfunction(m) and m.__code__.co_qualname.startswith(f"{cls.__qualname__}."))
    if (method := next(own, None)) is not None:
        file, line = Path(method.__code__.co_filename), method.__code__.co_firstlineno
    else:  # e.g. a `NamedTuple` with only fields
        file, (_, line) = Path(inspect.getsourcefile(cls) or ""), inspect.getsourcelines(cls)
    # Setting ``__module__`` also drops ``__firstlineno__``, so find the innermost ``class`` statement around the line.
    classes = (
        n
        for n in ast.walk(ast.parse(file.read_bytes()))
        if isinstance(n, ast.ClassDef) and _span(n)[0] <= line <= _span(n)[1]
    )
    # farthest down = innermost
    if (node := max(classes, key=lambda n: _span(n)[0], default=None)) is None:  # pragma: no cover
        return None
    return file, node


def _defines(stmt: ast.stmt, name: str) -> bool:
    """Whether `stmt` in a class body defines the attribute `name`."""
    match stmt:
        case ast.FunctionDef(name=n) | ast.AsyncFunctionDef(name=n) | ast.ClassDef(name=n):
            return n == name
        case ast.AnnAssign(target=ast.Name(id=n)):
            return n == name
        case ast.Assign(targets=targets):
            return any(isinstance(t, ast.Name) and t.id == name for t in targets)
    return False


def _locate_member(owner: type, name: str) -> Location | None:
    """Where the statements defining `name` in `owner`’s body are.

    Covers what :mod:`inspect` can’t: plain attributes, and descriptors whose getter is defined elsewhere.
    Spans all of them (e.g. a property’s setter, or overloads), and the docstring after an assignment.
    """
    if (found := _class_node(owner)) is None:  # pragma: no cover
        return None
    file, node = found
    if not (indices := [i for i, stmt in enumerate(node.body) if _defines(stmt, name)]):
        return None
    first, last = node.body[indices[0]], node.body[indices[-1]]
    match node.body[indices[-1] + 1 : indices[-1] + 2]:
        case [ast.Expr(value=ast.Constant(value=str())) as doc] if isinstance(last, ast.Assign | ast.AnnAssign):
            last = doc
    return Location(file, _span(first, last))


def _locate_type_alias(alias: TypeAliasType) -> Location | None:
    """Where a ``type`` statement is, which :mod:`inspect` can’t find."""
    if (module := alias.__module__) is None:  # pragma: no cover
        return None
    file = Path(inspect.getsourcefile(import_module(module)) or "")
    aliases = (
        n
        for n in ast.walk(ast.parse(file.read_bytes()))
        if isinstance(n, ast.TypeAlias) and n.name.id == alias.__name__
    )
    if (node := next(aliases, None)) is None:
        return None
    return Location(file, _span(node))
