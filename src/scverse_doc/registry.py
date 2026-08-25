"""The scverse package registry.

One mapping drives the “scverse packages” navbar dropdown,
the per-package accent colour, and `intersphinx_mapping`.

Its data is `scverse/ecosystem-packages`’ published `packages.json`_,
the same listing the website renders, fetched once per build and cached.
Only the accent colours are added here, because they live in the website’s SCSS instead.

.. _scverse/ecosystem-packages: https://github.com/scverse/ecosystem-packages
.. _packages.json: https://scverse.org/ecosystem-packages/packages.json
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from operator import itemgetter
from typing import TYPE_CHECKING, Any, Literal

from sphinx.util import requests

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

__all__ = ["Package", "core_packages", "intersphinx", "packages"]

#: The published upstream listing.
SOURCE = "https://scverse.org/ecosystem-packages/packages.json"

#: Where the fetched listing is cached.
#: The extension points this at the Sphinx build’s doctree directory – where intersphinx caches its inventories –
#: so cleaning the build directory drops it too.
#: :data:`None` fetches every time.
cache_dir: Path | None = None

#: How long a cached listing is reused before it is fetched again.
MAX_AGE_SECONDS = 24 * 60 * 60

#: The brand primary, used when a package has no accent of its own.
DEFAULT_ACCENT = "#4557c4"

#: Brand accents, transcribed from ``assets/main.scss`` in the website repository.
ACCENTS = {
    "anndata": "#e5864b",
    "mudata": "#4ab274",
    "muon": "#6cf1a1",
    "pertpy": "#da347f",
    "scanpy": "#de367b",
    "scirpy": "#da347f",
    "scvi-tools": "#fbb822",
    "spatialdata": "#40a9ff",
    "squidpy": "#969dea",
}

#: Upstream ``category`` -> the ``kind`` recorded here.
#: ``core-infrastructure`` is skipped:
#: those entries are repositories (governance, stats, the website), not packages.
KINDS: dict[str, Literal["core", "ecosystem"]] = {
    "core-datastructure": "core",
    "core-framework": "core",
    "ecosystem": "ecosystem",
}

#: Non-scverse inventories that essentially every scverse package needs.
EXTERNAL = {
    "python": "https://docs.python.org/3",
    "numpy": "https://numpy.org/doc/stable/",
    "scipy": "https://docs.scipy.org/doc/scipy/",
    "pandas": "https://pandas.pydata.org/docs/",
    "matplotlib": "https://matplotlib.org/stable/",
}


@dataclass(frozen=True, slots=True)
class Package:
    """One entry in the scverse package registry."""

    name: str
    """The package’s display name, e.g. ``"scvi-tools"``."""

    kind: Literal["core", "ecosystem"]
    """Whether the package is maintained by the core team or listed as an ecosystem package."""

    docs: str
    """Where to send a reader, exactly as the upstream listing records it.

    This is a link for humans,
    so it may name a particular page rather than a documentation root.
    """

    inventory: str | None = None
    """Root URL under which the package’s ``objects.inv`` resolves,
    or :data:`None` if it publishes no inventory.

    Distinct from :attr:`docs`:
    a versioned Read the Docs site serves its inventory and pages under ``en/stable/`` or the like,
    while its documentation home is the bare domain.
    """

    repo: str | None = None
    """URL of the source repository, if the upstream listing records one."""

    description: str = ""
    """One-line summary, as recorded upstream."""

    accent: str = DEFAULT_ACCENT
    """The package’s brand accent, falling back to the scverse primary."""


@cache
def _fetch() -> list[dict[str, Any]]:
    """Fetch the upstream listing, going through :data:`cache_dir` if one is set."""
    cached = cache_dir / "scverse-packages.json" if cache_dir is not None else None
    if cached is not None and cached.is_file() and time.time() - cached.stat().st_mtime < MAX_AGE_SECONDS:
        return json.loads(cached.read_text())
    try:
        response = requests.get(SOURCE, timeout=30)
        response.raise_for_status()
    except OSError:  # `requests.RequestException` is an `OSError`, so this covers both it and the file system
        if cached is not None and cached.is_file():
            return json.loads(cached.read_text())  # a stale listing beats failing the build
        raise
    if cached is not None:
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(response.content)
    listing: list[dict[str, Any]] = response.json()
    return listing


@cache
def _load() -> Mapping[str, Package]:
    """Build the registry from the upstream listing, keyed and sorted by case-folded name."""
    return {
        name: Package(
            name=meta["name"],
            kind=kind,
            docs=meta["documentation_home"],  # verbatim: upstream picked this page for human readers
            inventory=meta.get("inventory"),
            repo=meta.get("project_home"),
            description=" ".join(meta.get("description", "").split()),
            accent=ACCENTS.get(name, DEFAULT_ACCENT),
        )
        # Sorted here, because upstream’s listing order is not stable.
        for name, meta in sorted(((meta["name"].casefold(), meta) for meta in _fetch()), key=itemgetter(0))
        if (kind := KINDS.get(meta.get("category", "")))
    }


class Packages(Mapping[str, Package]):
    """Every registered package, looked up case-insensitively."""

    def __getitem__(self, name: str) -> Package:
        return _load()[name.casefold()]

    def __iter__(self) -> Iterator[str]:
        return iter(_load())

    def __len__(self) -> int:
        return len(_load())


#: Every registered package, keyed and ordered by case-folded name.
packages: Mapping[str, Package] = Packages()


def core_packages() -> Mapping[str, Package]:
    """Return only the core packages."""
    return {name: pkg for name, pkg in packages.items() if pkg.kind == "core"}


def intersphinx(*extra: str, external: bool = True, core: bool = True) -> dict[str, tuple[str, None]]:
    """Build an `intersphinx_mapping` for this package.

    Deliberately not “every scverse package by default”:
    each entry is an inventory fetched on every build,
    and all 100+ of them would make a cold docs build slow
    and give it 100+ chances to fail on someone else’s outage.
    The default is the handful of packages that almost every scverse docs build actually links to,
    and anything else is opted into by name.

    Parameters
    ----------
    extra
        Additional registry package names to include, e.g. ``intersphinx("scanpy", "muon")``.
        Unknown names raise,
        so a typo or a renamed package fails the build instead of silently dropping links.
    external
        Whether to include the non-scverse inventories (Python, NumPy, SciPy, pandas, Matplotlib).
    core
        Whether to include the core packages that publish an inventory.

    Returns
    -------
    A mapping ready to assign to `intersphinx_mapping`.

    Raises
    ------
    KeyError
        If a name in `extra` is not in the registry.
    ValueError
        If a name in `extra` is registered but publishes no ``objects.inv`` to link against.

    Examples
    --------
    >>> mapping = intersphinx("scanpy")
    >>> mapping["scanpy"]  # doctest: +ELLIPSIS
    ('https://scanpy.scverse.org/...', None)
    """
    mapping: dict[str, tuple[str, None]] = {}
    if external:
        mapping.update({name: (url, None) for name, url in EXTERNAL.items()})

    core_names = (name for name, pkg in core_packages().items() if pkg.inventory) if core else ()
    names: Iterable[str] = (*core_names, *extra)
    for name in names:
        if (pkg := packages.get(name)) is None:
            msg = f"{name!r} is not in the scverse registry. Known packages: {', '.join(packages)}"
            raise KeyError(msg)
        if pkg.inventory is None:
            msg = f"{pkg.name} publishes no objects.inv at {pkg.docs}, so there is nothing to link against."
            raise ValueError(msg)
        # Key on the requested name so `:doc:`scanpy:...`` reads the way the author wrote it.
        mapping[name] = (pkg.inventory, None)
    return mapping
