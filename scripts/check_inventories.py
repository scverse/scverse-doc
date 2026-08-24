#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx2", "httpx-limiter[aiolimiter]", "httpx-retries>=0.6", "pyyaml", "scverse-doc"]
#
# [tool.uv.sources]
# scverse-doc = { path = "..", editable = true }
# ///
"""Check that every registry package still publishes a reachable ``objects.inv``.

Cross-package links break silently today: a package moves its documentation, and every other package's links to it
rot without anything failing.
This runs nightly so the registry finds out before readers do.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import TYPE_CHECKING

import httpx2

# Its sibling owns how we talk to documentation sites: rate limited per host, retried, redirects followed.
from build_registry import client

from scverse_doc.registry import Package, core_packages, packages

if TYPE_CHECKING:
    from collections.abc import Iterable


async def probe(http: httpx2.AsyncClient, pkg: Package) -> tuple[Package, str]:
    """Return the package and either ``"ok"`` or a description of what went wrong."""
    try:
        response = await http.head(f"{pkg.inventory}objects.inv")
    except httpx2.HTTPError as e:
        return pkg, f"{type(e).__name__}: {e}"
    return pkg, "ok" if response.is_success else f"HTTP {response.status_code}"


async def probe_all(selected: Iterable[Package]) -> list[tuple[Package, str]]:
    """Probe every selected inventory concurrently."""
    async with client() as http:
        return await asyncio.gather(*(probe(http, pkg) for pkg in selected))


def main() -> int:
    """Probe every selected inventory and report the failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-only", action="store_true", help="skip the ecosystem packages")
    args = parser.parse_args()

    selected = (core_packages() if args.core_only else packages()).values()
    # Packages that publish no inventory have no cross-package links to rot, and build_registry.py already named
    # them. Probing them anyway is what used to make this report permanently red.
    linkable = [pkg for pkg in selected if pkg.inventory]
    results = sorted(asyncio.run(probe_all(linkable)), key=lambda r: r[0].name.lower())

    failures = [(pkg, status) for pkg, status in results if status != "ok"]
    skipped = f", {n} publish none" if (n := len(selected) - len(linkable)) else ""
    print(f"## Inventories\n\n{len(results) - len(failures)}/{len(results)} reachable{skipped}\n")
    for pkg, status in failures:
        print(f"- **{pkg.name}** – `{pkg.inventory}objects.inv` – {status}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
