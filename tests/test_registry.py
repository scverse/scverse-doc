"""The generated registry and the intersphinx mapping built from it."""

from __future__ import annotations

import pytest

from scverse_doc.registry import core_packages, get, intersphinx, packages

CORE = {
    "anndata",
    "decoupler",
    "mudata",
    "muon",
    "pertpy",
    "rapids-singlecell",
    "scanpy",
    "scirpy",
    "scvi-tools",
    "snapatac2",
    "spatialdata",
    "squidpy",
}


def test_core_packages_are_the_ones_the_website_lists() -> None:
    assert set(core_packages()) == CORE


def test_entries_are_well_formed() -> None:
    for pkg in packages().values():
        # ``docs`` is upstream's link for humans, so it may well name a page. An inventory root may not.
        assert pkg.docs.startswith("https://"), pkg
        assert pkg.accent.startswith("#"), pkg
        if pkg.inventory is not None:
            assert pkg.inventory.startswith("https://"), pkg
            assert pkg.inventory.endswith("/"), pkg
            assert "#" not in pkg.inventory, pkg


def test_every_core_package_is_linkable() -> None:
    for pkg in core_packages().values():
        assert pkg.inventory is not None, pkg


def test_intersphinx_covers_core_and_keeps_the_ecosystem_opt_in() -> None:
    mapping = intersphinx()
    assert CORE <= set(mapping)
    assert "python" in mapping
    assert "annsel" not in mapping
    assert "annsel" in intersphinx("annsel")


def test_unknown_extra_fails_loudly() -> None:
    with pytest.raises(KeyError, match="not in the scverse registry"):
        intersphinx("scnapy")


def test_lookup_is_case_insensitive() -> None:
    assert get("SNAPATAC2") is get("SnapATAC2")
    assert get("nope") is None
