#!/usr/bin/env python
"""Regenerate `scverse_doc/registry.json` from the upstream sources of truth.

There are two of them, and neither is this repository:

- `scverse/ecosystem-packages <https://github.com/scverse/ecosystem-packages>`_ holds one schema-validated
  ``packages/<Name>/meta.yaml`` per ecosystem package, including its ``documentation_home``.
- The website's ``content/packages/_index.md`` holds the core packages as Hugo TOML front matter.

Hand-maintaining a third list would guarantee it drifts from those two, so this script derives the registry instead.
Only the per-package accent colours are curated here, because they live in the website's SCSS rather than in either
package listing.

Usage
-----
    python scripts/build_registry.py --ecosystem ../ecosystem-packages --website ../scverse.github.io
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

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

#: Canonical documentation URLs, where the upstream listing records a landing page, an outdated host, or a
#: version scheme its ``objects.inv`` does not live under. Verified against the live sites.
CANONICAL_DOCS = {
    "anndata": "https://anndata.scverse.org/en/stable/",
    "mudata": "https://mudata.readthedocs.io/stable/",
    "scanpy": "https://scanpy.scverse.org/en/stable/",
    "scirpy": "https://scirpy.scverse.org/en/stable/",
    "scvi-tools": "https://docs.scvi-tools.org/en/stable/",
    "spatialdata": "https://spatialdata.scverse.org/en/stable/",
    "squidpy": "https://squidpy.readthedocs.io/en/stable/",
}

#: Non-scverse inventories that essentially every scverse package needs.
EXTERNAL = {
    "python": "https://docs.python.org/3",
    "numpy": "https://numpy.org/doc/stable/",
    "scipy": "https://docs.scipy.org/doc/scipy/",
    "pandas": "https://pandas.pydata.org/docs/",
    "matplotlib": "https://matplotlib.org/stable/",
}


def _iter_core(website: Path) -> Iterator[dict[str, Any]]:
    """Yield core package entries from the website's Hugo front matter."""
    text = (website / "content" / "packages" / "_index.md").read_text()
    if (m := re.search(r"\A\+\+\+\n(.*?)\n\+\+\+", text, re.DOTALL)) is None:
        msg = f"No TOML front matter in {website}/content/packages/_index.md"
        raise ValueError(msg)
    data = tomllib.loads(m[1])
    for section in ("datastructures", "packages"):
        for entry in data.get(section, []):
            links = {link["text"].lower(): link["url"] for link in entry.get("links", [])}
            yield {
                "name": entry["name"],
                "kind": "core",
                "docs": links.get("documentation", entry["url"]),
                "repo": links.get("github"),
                "description": entry.get("description", ""),
            }


def _iter_ecosystem(ecosystem: Path) -> Iterator[dict[str, Any]]:
    """Yield ecosystem package entries from `scverse/ecosystem-packages` metadata."""
    for meta_path in sorted((ecosystem / "packages").glob("*/meta.yaml")):
        meta = yaml.safe_load(meta_path.read_text())
        if not (docs := meta.get("documentation_home")):
            continue
        yield {
            "name": meta["name"],
            "kind": "ecosystem",
            "docs": docs,
            "repo": meta.get("project_home"),
            "description": " ".join(meta.get("description", "").split()),
        }


def build(ecosystem: Path, website: Path) -> dict[str, Any]:
    """Build the registry mapping from both upstream sources.

    Core entries win over ecosystem entries of the same name, since a package listed in both is core.
    """
    packages: dict[str, dict[str, Any]] = {}
    for entry in (*_iter_ecosystem(ecosystem), *_iter_core(website)):
        entry["docs"] = entry["docs"].rstrip("/") + "/"
        if accent := ACCENTS.get(entry["name"].lower()):
            entry["accent"] = accent
        entry["docs"] = CANONICAL_DOCS.get(entry["name"].lower(), entry["docs"])
        packages[entry["name"]] = entry
    # Every core package is cross-linkable out of the box: they are the ones scverse docs actually link to, and the
    # ecosystem's 80 entries stay opt-in so a cold build does not fetch 92 inventories.
    core = [name for name, entry in packages.items() if entry["kind"] == "core"]
    return {
        "$comment": "GENERATED by scripts/build_registry.py — do not edit by hand.",
        "core_intersphinx": core,
        "external": EXTERNAL,
        "packages": dict(sorted(packages.items(), key=lambda kv: kv[0].lower())),
    }


def main() -> int:
    """Write the regenerated registry to disk."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ecosystem", type=Path, required=True, help="checkout of scverse/ecosystem-packages")
    parser.add_argument("--website", type=Path, required=True, help="checkout of scverse/scverse.github.io")
    parser.add_argument("--check", action="store_true", help="fail instead of writing if the output would change")
    args = parser.parse_args()

    registry = build(args.ecosystem, args.website)
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
