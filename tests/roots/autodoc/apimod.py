# SPDX-License-Identifier: MPL-2.0
"""A module to document."""

from typing import Generic, TypeVar

T = TypeVar("T")


class _Private:
    pass


class Public:
    """A public base."""


class Thing(_Private, Public, Generic[T]):  # noqa: UP046
    """A thing."""

    attr: int = 1
    """An attribute."""

    ivar: str
    """An instance attribute, which only autosummary’s fallback for dotted names finds."""

    @property
    def prop(self) -> int:
        """A property."""
        return 1

    def meth(self) -> None:
        """A method."""


def fit() -> None:
    """Fit something.

    Returns
    -------
    The fitted model, or `None` if `copy` is false.
    """


def split() -> tuple[int, Public] | None:
    """Split something.

    Returns
    -------
    count
        How many.
    thing
        Which one.
    """
