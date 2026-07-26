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
    "SnapATAC2",
    "spatialdata",
    "squidpy",
}


def test_core_packages_are_the_ones_the_website_lists() -> None:
    assert set(core_packages()) == CORE


def test_entries_are_well_formed() -> None:
    for pkg in packages().values():
        assert pkg.docs.startswith("https://"), pkg
        assert pkg.docs.endswith("/"), pkg
        assert pkg.accent.startswith("#"), pkg


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
