#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "httpx-limiter[aiolimiter]", "httpx-retries", "pyyaml"]
# ///
"""Regenerate `scverse_doc/registry.json` from the upstream source of truth.

That source is `scverse/ecosystem-packages <https://github.com/scverse/ecosystem-packages>`_, which holds one
schema-validated ``packages/<Name>/meta.yaml`` per package – including its ``documentation_home`` and its
``category``, which is what makes a package core.
The website is *downstream* of it too: ``layouts/packages/list.html`` renders the package pages from the
registry's published ``packages.json``.

Hand-maintaining a second list would guarantee it drifts from that one, so this script derives the registry
instead.
Only the per-package accent colours are curated here, because they live in the website's SCSS rather than in the
package metadata.

Usage
-----
    uv run scripts/build_registry.py --ecosystem ../ecosystem-packages
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, override

import httpx
import yaml
from httpx_limiter import AbstractRateLimiterRepository, AsyncMultiRateLimitedTransport, Rate
from httpx_limiter.aiolimiter import AiolimiterAsyncLimiter
from httpx_retries import Retry, RetryTransport

if TYPE_CHECKING:
    from collections.abc import Iterator

HERE = Path(__file__).parent
TARGET = HERE.parent / "src" / "scverse_doc" / "registry.json"

#: Brand accents, transcribed from ``assets/main.scss`` in the website repository.
#: These are not derivable from either package listing, so they are curated here and checked by
#: ``tests/test_registry.py`` against the SCSS when a checkout is available.
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

#: Read the Docs and Cloudflare answer 403 to httpx's default agent.
USER_AGENT = "scverse-doc registry check (+https://github.com/scverse/scverse-doc)"

#: Upstream ``category`` -> the ``kind`` recorded here.
#: ``core-infrastructure`` is deliberately absent: those entries are scverse's own repositories (governance, stats,
#: the website) rather than packages, and the website's own listing skips them for the same reason.
KINDS = {
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


def _iter_packages(ecosystem: Path) -> Iterator[dict[str, Any]]:
    """Yield package entries from `scverse/ecosystem-packages` metadata."""
    for meta_path in sorted((ecosystem / "packages").glob("*/meta.yaml")):
        meta = yaml.safe_load(meta_path.read_text())
        kind = KINDS.get(meta.get("category", ""))
        if not kind or not (docs := meta.get("documentation_home")):
            continue
        yield {
            "name": meta["name"],
            "kind": kind,
            "docs": docs,  # verbatim: upstream picked this page for human readers
            "inventory": None,  # filled in by `build`, which has to ask the site
            "repo": meta.get("project_home"),
            "description": " ".join(meta.get("description", "").split()),
        }


async def _inventory_root(http: httpx.AsyncClient, docs: str) -> str | None:
    """Return the documentation root whose ``objects.inv`` resolves, or `None` if the package publishes no inventory.

    This is *not* ``documentation_home``, which is a link for humans: upstream is free to point it at whichever page
    reads best (``…/page/api.html``, say), and on a versioned Read the Docs site it is the bare domain while both
    the inventory and every page it points at live under ``en/stable/`` or the like.
    So strip any chosen page back to the site root, then ask Read the Docs' ``/page/`` redirect which version the
    project currently serves, rather than pinning one by hand.
    Single-version sites (mkdocs on GitHub Pages, say) have no ``/page/`` and are already their own root, so those
    are used exactly as upstream wrote them — following their redirects too would inherit any http:// downgrade a
    redirect stub happens to have been written with.
    """
    # A fragment or query is never part of a path, and leaving one on would append the probe to it instead: a
    # ``…/repo#readme/page/objects.inv`` request reaches the server as ``…/repo``, which happily answers 200.
    root = re.split(r"[#?]", docs)[0].split("/page/")[0].rstrip("/") + "/"
    for candidate, resolve in ((f"{root}page/", True), (root, False)):
        try:
            response = await http.head(f"{candidate}objects.inv")
        except httpx.HTTPError:
            continue
        if response.is_success:
            # ``response.url`` is where the redirect landed, i.e. the version the project currently serves.
            return str(response.url).removesuffix("objects.inv") if resolve else candidate
    return None


class DomainRateLimiters(AbstractRateLimiterRepository):
    """Rate-limit per host, so that the thirty packages on readthedocs.io do not arrive there all at once."""

    @override
    def get_identifier(self, request: httpx.Request) -> str:
        return request.url.host

    @override
    def create(self, request: httpx.Request) -> AiolimiterAsyncLimiter:
        return AiolimiterAsyncLimiter.create(Rate.create(magnitude=25))


def client() -> httpx.AsyncClient:
    """An HTTP client that survives a flaky mirror, since its answers get committed to the registry.

    Same shape as the one in ecosystem-packages' ``validate_registry``, for the same reason: a global connection cap
    would throttle the hundred *other* hosts too, and it is per-host politeness that these sites care about.
    """
    transport = AsyncMultiRateLimitedTransport.create(repository=DomainRateLimiters())
    return httpx.AsyncClient(
        follow_redirects=True,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
        transport=RetryTransport(transport, Retry(total=3, backoff_factor=2)),
    )


async def build(ecosystem: Path) -> dict[str, Any]:
    """Build the registry mapping from the upstream package metadata."""
    entries = list(_iter_packages(ecosystem))
    async with client() as http:
        roots = await asyncio.gather(*(_inventory_root(http, entry["docs"]) for entry in entries))

    packages: dict[str, dict[str, Any]] = {}
    for entry, root in zip(entries, roots, strict=True):
        name = entry["name"].casefold()
        entry["inventory"] = root
        if root is None:
            print(f"no objects.inv for {entry['name']} under {entry['docs']}", file=sys.stderr)
        if accent := ACCENTS.get(name):
            entry["accent"] = accent
        packages[name] = entry
    # Every core package is cross-linkable out of the box: they are the ones scverse docs actually link to, and
    # the ecosystem's hundred entries stay opt-in so a cold build does not fetch all 113 inventories.
    core = [name for name, entry in packages.items() if entry["kind"] == "core" and entry["inventory"]]
    return {
        "$comment": "GENERATED by scripts/build_registry.py – do not edit by hand.",
        "core_intersphinx": core,
        "external": EXTERNAL,
        "packages": dict(sorted(packages.items())),
    }


def main() -> int:
    """Write the regenerated registry to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ecosystem", type=Path, required=True, help="checkout of scverse/ecosystem-packages")
    parser.add_argument("--check", action="store_true", help="fail instead of writing if the output would change")
    args = parser.parse_args()

    registry = asyncio.run(build(args.ecosystem))
    rendered = json.dumps(registry, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if TARGET.read_text() != rendered:
            print(f"{TARGET} is out of date; rerun scripts/build_registry.py", file=sys.stderr)
            return 1
        return 0
    TARGET.write_text(rendered)
    print(f"wrote {len(registry['packages'])} packages to {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
