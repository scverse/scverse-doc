"""The generated registry and the intersphinx mapping built from it."""

from __future__ import annotations

import pytest

from scverse_doc.registry import DEFAULT_ACCENT, Package, core_packages, get, intersphinx, packages


def require(name: str) -> Package:
    pkg = get(name)
    assert pkg is not None, name
    return pkg


def test_registry_is_populated() -> None:
    assert len(packages()) > 50
    assert set(core_packages()) < set(packages())


def test_core_packages_are_the_ones_the_website_lists() -> None:
    assert set(core_packages()) == {
        "anndata",
        "decoupler",
        "mudata",
        "muon",
        "pertpy",
        "rapids-singlecell",
        "scanpy",
        "scirpy",
        "scvi-tools",
        "SnapATAC2",
        "spatialdata",
        "squidpy",
    }


@pytest.mark.parametrize("pkg", packages().values(), ids=lambda p: p.name)
def test_entries_are_well_formed(pkg: Package) -> None:
    assert pkg.docs.startswith("https://")
    assert pkg.docs.endswith("/")
    assert pkg.kind in {"core", "ecosystem"}
    assert pkg.accent.startswith("#")


def test_lookup_is_case_insensitive() -> None:
    assert get("SNAPATAC2") is get("SnapATAC2")
    assert get("nope") is None


def test_accent_defaults_to_the_brand_primary() -> None:
    assert require("annsel").accent == DEFAULT_ACCENT
    assert require("scanpy").accent == "#de367b"


def test_inventory_override_is_used_where_the_listed_url_is_wrong() -> None:
    mudata = require("mudata")
    assert mudata.docs != mudata.inventory[0]
    assert mudata.inventory[0] == "https://mudata.readthedocs.io/stable/"


def test_intersphinx_contains_every_core_package() -> None:
    mapping = intersphinx()
    assert set(core_packages()) <= set(mapping)
    assert "python" in mapping


def test_intersphinx_stays_opt_in_for_the_ecosystem() -> None:
    mapping = intersphinx()
    assert "annsel" not in mapping
    assert "annsel" in intersphinx("annsel")


def test_unknown_extra_fails_loudly() -> None:
    with pytest.raises(KeyError, match="not in the scverse registry"):
        intersphinx("scnapy")


def test_external_can_be_dropped() -> None:
    assert "python" not in intersphinx(external=False)
