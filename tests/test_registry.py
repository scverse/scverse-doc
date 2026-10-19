# SPDX-License-Identifier: MPL-2.0
"""The fetched registry and the intersphinx mapping built from it."""

from __future__ import annotations

import json
import os
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
import requests

from scverse_doc import registry
from scverse_doc.registry import core_packages, intersphinx, packages

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

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
    for pkg in packages.values():
        # ``docs`` is upstream’s link for humans, so it may well name a page.
        # An inventory root may not.
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
    mapping = intersphinx("scnapy")  # lazy: nothing is resolved yet
    with pytest.raises(KeyError, match="not in the scverse registry"):
        dict(mapping)


def test_intersphinx_does_not_touch_the_registry_before_it_is_read(monkeypatch: pytest.MonkeyPatch) -> None:
    # A `conf.py` calls `intersphinx` before the extension sets `cache_dir`, so the registry must stay untouched.
    for name in ("_fetch", "_load"):
        monkeypatch.setattr(registry, name, pytest.fail)
    intersphinx("annsel")


def test_lookup_is_case_insensitive() -> None:
    assert packages["SNAPATAC2"] is packages["SnapATAC2"]
    assert "nope" not in packages


@pytest.fixture
def cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point the registry at an empty cache directory, and leave the real one behind for the other tests."""
    monkeypatch.setattr(registry, "_cache_dir", tmp_path)
    for fn in (registry._fetch, registry._load):
        fn.cache_clear()
    yield tmp_path
    for fn in (registry._fetch, registry._load):
        fn.cache_clear()


def test_listing_is_cached_and_reused(cache_dir: Path) -> None:
    cached = cache_dir / "scverse-packages.json"
    listing = registry._fetch()
    assert json.loads(cached.read_text()) == listing  # written on the first fetch

    cached.write_text('[{"name": "Zzz", "category": "ecosystem", "documentation_home": "https://example.com/"}]')
    registry._fetch.cache_clear()
    assert set(packages) == {"zzz"}  # read back instead of refetched


def test_stale_listing_beats_a_failed_fetch(cache_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def offline(*_: object, **__: object) -> None:
        raise requests.ConnectionError

    monkeypatch.setattr(registry.requests, "get", offline)
    with pytest.raises(requests.ConnectionError):
        registry._fetch()

    cached = cache_dir / "scverse-packages.json"
    cached.write_text("[]")
    os.utime(cached, (0, 0))
    assert registry._fetch() == []


def test_mappings_have_a_length() -> None:
    assert len(packages) == len(list(packages))
    assert len(registry._RegistryInventories(("annsel",), core=False)) == 1


def test_extra_without_inventory_fails_loudly() -> None:
    name = next(pkg.name for pkg in packages.values() if pkg.inventory is None)
    with pytest.raises(ValueError, match="publishes no objects.inv"):
        dict(intersphinx(name))


@pytest.mark.parametrize(
    ("raw", "mapping", "expected"),
    [
        pytest.param({}, None, dict(intersphinx()), id="default"),
        pytest.param({"intersphinx_mapping": ...}, intersphinx("annsel"), dict(intersphinx("annsel")), id="chainmap"),
        pytest.param({"intersphinx_mapping": ...}, {"x": ("y", None)}, {"x": ("y", None)}, id="dict"),
    ],
)
def test_configure_intersphinx(raw: dict[str, object], mapping: object, expected: object) -> None:
    config = SimpleNamespace(_raw_config=raw, _overrides={}, intersphinx_mapping=mapping)
    registry._configure_intersphinx(None, config)  # type: ignore[arg-type]
    assert config.intersphinx_mapping == expected
    assert type(config.intersphinx_mapping) is dict
