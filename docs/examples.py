# SPDX-License-Identifier: MPL-2.0
"""Example objects that the API pages document, to show off the subextensions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import ThreadPoolExecutor


def split(items: list[str], frac: float = 0.8) -> tuple[list[str], list[str]]:
    """Split `items` into a training and a test set.

    Returns
    -------
    train
        The first `frac` of `items`.
    test
        The rest.
    """
    n = round(len(items) * frac)
    return items[:n], items[n:]


def find(items: list[str], item: str) -> int | None:
    """Find `item` in `items`.

    Returns
    -------
    The index of `item`, or `None` if it isn’t in `items`.
    """
    return items.index(item) if item in items else None


def run(fn: Callable[[], object], executor: ThreadPoolExecutor) -> object:
    """Run `fn` in `executor` and wait for the result."""
    return executor.submit(fn).result()


class Model:
    """A model with an attribute, a property and a method."""

    #: How many items to fit at once.
    batch_size: int = 32

    @property
    def fitted(self) -> bool:
        """Whether :meth:`fit` has been called."""
        return hasattr(self, "_items")

    def fit(self, items: list[str]) -> None:
        """Fit the model to `items`."""
        self._items = items
