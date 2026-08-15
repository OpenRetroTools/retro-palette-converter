"""Cross-registry consistency tests for the completed M2.3 architecture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from retropal.palettes import PALETTE_IDS, iter_palette_info
from retropal.palettes.fixed import (
    REQUIRED_METADATA_FIELDS,
    _fixed_palettes,
    fixed_palette_ids,
    load_fixed_palette,
)
from retropal.palettes.inventory import inventory_markdown
from retropal.palettes.profiles import (
    PlatformProfile,
    _index_profiles,
    iter_platform_profiles,
)


def test_every_profile_references_registered_palettes() -> None:
    registered = set(PALETTE_IDS)
    for profile in iter_platform_profiles():
        assert profile.palette_ids
        assert set(profile.palette_ids) <= registered
        assert profile.default_palette_id in profile.palette_ids


def test_every_palette_exposes_consistent_metadata() -> None:
    ids: set[str] = set()
    names: set[str] = set()
    for info in iter_palette_info():
        assert info.id not in ids
        assert info.name.casefold() not in names
        ids.add(info.id)
        names.add(info.name.casefold())
        assert info.manufacturer
        assert info.platform
        assert info.family
        assert info.year is not None and info.year > 0
        assert info.color_count > 0
        assert info.bit_depth
        assert info.palette_source
        assert info.tags
        assert info.notes


def test_every_json_definition_uses_canonical_schema() -> None:
    root = Path(__file__).parents[1] / "src/retropal/palettes/definitions"
    definitions = sorted(root.glob("*.json"))
    assert {path.stem for path in definitions} == set(fixed_palette_ids())
    for path in definitions:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload.keys() >= REQUIRED_METADATA_FIELDS
        assert "name" not in payload
        assert payload["id"] == path.stem


def test_duplicate_fixed_palette_ids_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path(__file__).parents[1] / "src/retropal/palettes/definitions/gameboy.json"
    payload = json.loads(original.read_text(encoding="utf-8"))
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(payload), encoding="utf-8")
    second.write_text(json.dumps(payload | {"display_name": "A different name"}), encoding="utf-8")
    monkeypatch.setattr("retropal.palettes.fixed._definition_resources", lambda: (first, second))
    _fixed_palettes.cache_clear()
    with pytest.raises(ValueError, match="Duplicate palette ID"):
        _fixed_palettes()
    _fixed_palettes.cache_clear()


def test_duplicate_fixed_palette_display_names_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path(__file__).parents[1] / "src/retropal/palettes/definitions/gameboy.json"
    payload = json.loads(original.read_text(encoding="utf-8"))
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(payload), encoding="utf-8")
    second.write_text(json.dumps(payload | {"id": "different-id"}), encoding="utf-8")
    monkeypatch.setattr("retropal.palettes.fixed._definition_resources", lambda: (first, second))
    _fixed_palettes.cache_clear()
    with pytest.raises(ValueError, match="Duplicate palette display name"):
        _fixed_palettes()
    _fixed_palettes.cache_clear()


def test_fixed_palette_alias_target_must_exist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = Path(__file__).parents[1] / "src/retropal/palettes/definitions/gameboy.json"
    payload = json.loads(original.read_text(encoding="utf-8"))
    definition = tmp_path / "gameboy.json"
    definition.write_text(json.dumps(payload | {"alias_of": "missing"}), encoding="utf-8")
    monkeypatch.setattr("retropal.palettes.fixed._definition_resources", lambda: (definition,))
    _fixed_palettes.cache_clear()
    with pytest.raises(ValueError, match="aliases unknown palette"):
        _fixed_palettes()
    _fixed_palettes.cache_clear()


def test_fixed_palette_alias_colors_must_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = Path(__file__).parents[1] / "src/retropal/palettes/definitions"
    alias_payload = json.loads((root / "gameboy.json").read_text(encoding="utf-8"))
    target_payload = json.loads((root / "gameboy-dmg.json").read_text(encoding="utf-8"))
    alias_payload["colors"][0] = [0, 0, 0]
    alias = tmp_path / "gameboy.json"
    target = tmp_path / "gameboy-dmg.json"
    alias.write_text(json.dumps(alias_payload), encoding="utf-8")
    target.write_text(json.dumps(target_payload), encoding="utf-8")
    monkeypatch.setattr("retropal.palettes.fixed._definition_resources", lambda: (alias, target))
    _fixed_palettes.cache_clear()
    with pytest.raises(ValueError, match="does not match alias target"):
        _fixed_palettes()
    _fixed_palettes.cache_clear()


def test_duplicate_profile_ids_are_rejected() -> None:
    profile = iter_platform_profiles()[0]
    with pytest.raises(ValueError, match="Duplicate platform profile ID"):
        _index_profiles((profile, profile))


def test_generated_inventory_contains_every_profile_palette() -> None:
    inventory = inventory_markdown()
    for profile in iter_platform_profiles():
        for palette_id in profile.palette_ids:
            assert f"| {profile.platform} | {profile.name} | {palette_id} |" in inventory


def test_legacy_palette_aliases_are_explicit_and_equivalent() -> None:
    aliases = {"gameboy": "gameboy-dmg", "ega": "ega-default"}
    assert {
        info.id: info.alias_of for info in iter_palette_info() if info.alias_of is not None
    } == aliases
    for legacy_id, canonical_id in aliases.items():
        assert load_fixed_palette(legacy_id).colors == load_fixed_palette(canonical_id).colors
        assert f"| `{legacy_id}` | `{canonical_id}` |" in inventory_markdown()


def test_profile_type_is_immutable() -> None:
    assert PlatformProfile.__dataclass_params__.frozen
    assert set(PALETTE_IDS) == {info.id for info in iter_palette_info()}
