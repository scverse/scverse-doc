#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["scverse-doc"]
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
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scverse_doc.registry import Package, core_packages, packages

# Read the Docs and Cloudflare answer 403 to urllib's default agent.
USER_AGENT = "scverse-doc registry check (+https://github.com/scverse/scverse-doc)"


def probe(pkg: Package) -> tuple[Package, str]:
    """Return the package and either ``"ok"`` or a description of what went wrong."""
    url = pkg.inventory[0] + "objects.inv"
    try:
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=30) as response:
            return pkg, "ok" if response.status == 200 else f"HTTP {response.status}"
    except HTTPError as e:
        return pkg, f"HTTP {e.code}"
    except (URLError, TimeoutError, OSError) as e:
        return pkg, f"{type(e).__name__}: {e}"


def main() -> int:
    """Probe every selected inventory and report the failures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-only", action="store_true", help="skip the 80 ecosystem packages")
    args = parser.parse_args()

    selected = (core_packages() if args.core_only else packages()).values()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = sorted(pool.map(probe, selected), key=lambda r: r[0].name.lower())

    failures = [(pkg, status) for pkg, status in results if status != "ok"]
    print(f"## Inventories\n\n{len(results) - len(failures)}/{len(results)} reachable\n")
    for pkg, status in failures:
        print(f"- **{pkg.name}** – `{pkg.inventory[0]}objects.inv` – {status}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
