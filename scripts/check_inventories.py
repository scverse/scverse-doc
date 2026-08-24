#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx2", "httpx-limiter[aiolimiter]", "httpx-retries>=0.6", "scverse-doc"]
#
# [tool.uv.sources]
# scverse-doc = { path = "..", editable = true }
# ///
"""Check that every registry package still publishes a reachable ``objects.inv``.

A package moving its documentation rots every other package's links to it without failing anything, so this runs
nightly.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import TYPE_CHECKING, override

import httpx2

# `httpx-limiter` and `httpx-retries` are written against `httpx`
sys.modules["httpx"] = httpx2

from httpx_limiter import AbstractRateLimiterRepository, AsyncMultiRateLimitedTransport, Rate  # noqa: E402
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter  # noqa: E402
from httpx_retries import Retry, RetryTransport  # noqa: E402

from scverse_doc.registry import Package, core_packages, packages  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterable

#: Read the Docs and Cloudflare answer 403 to httpx's default agent.
USER_AGENT = "scverse-doc registry check (+https://github.com/scverse/scverse-doc)"


class DomainRateLimiters(AbstractRateLimiterRepository):
    """Rate-limit per host, so that the thirty packages on readthedocs.io do not arrive there all at once."""

    @override
    def get_identifier(self, request: httpx2.Request) -> str:
        return request.url.host

    @override
    def create(self, request: httpx2.Request) -> AiolimiterAsyncLimiter:
        return AiolimiterAsyncLimiter.create(Rate.create(magnitude=25))


def client() -> httpx2.AsyncClient:
    """Build the client: rate limited per host, retried so a blip is not reported as a broken inventory."""
    transport = AsyncMultiRateLimitedTransport.create(repository=DomainRateLimiters())
    return httpx2.AsyncClient(
        follow_redirects=True,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
        transport=RetryTransport(transport, Retry(total=3, backoff_factor=2)),
    )


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
    # Packages publishing no inventory have no links to rot; probing them anyway would keep this report red.
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
