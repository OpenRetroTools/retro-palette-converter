"""Tests for the M2.3d Nintendo platform pack."""

from __future__ import annotations

from retropal.palettes import PALETTE_IDS, get_palette_info, list_by_family
from retropal.palettes.fixed import load_fixed_palette
from retropal.palettes.profiles import get_platform_profile, iter_platform_profiles

NINTENDO_PALETTE_IDS = (
    "nes-default",
    "gameboy-dmg",
    "gameboy-pocket",
    "gameboy-color",
    "snes-default",
)

NINTENDO_PROFILE_PALETTES = {
    "nintendo-nes": "nes-default",
    "nintendo-game-boy": "gameboy-dmg",
    "nintendo-game-boy-pocket": "gameboy-pocket",
    "nintendo-game-boy-color": "gameboy-color",
    "nintendo-snes": "snes-default",
}

EXPECTED_COLOR_COUNTS = {
    "nes-default": 64,
    "gameboy-dmg": 4,
    "gameboy-pocket": 4,
    "gameboy-color": 32,
    "snes-default": 64,
}


def test_nintendo_palette_ids_are_registered_and_loadable() -> None:
    assert set(NINTENDO_PALETTE_IDS) <= set(PALETTE_IDS)
    for palette_id in NINTENDO_PALETTE_IDS:
        palette = load_fixed_palette(palette_id)
        assert palette.id == palette_id
        assert len(palette.colors) == EXPECTED_COLOR_COUNTS[palette_id]


def test_nintendo_palette_metadata() -> None:
    for palette_id in NINTENDO_PALETTE_IDS:
        info = get_palette_info(palette_id)
        assert info.manufacturer == "Nintendo"
        assert info.family == "Nintendo"
        assert info.platform
        assert info.platform_family in {"Game Boy", "Nintendo home console"}
        assert info.generation
        assert info.year is not None
        assert info.color_count == EXPECTED_COLOR_COUNTS[palette_id]
        assert "nintendo" in info.tags
        assert info.notes


def test_nintendo_family_lookup_includes_new_pack_and_legacy_palette() -> None:
    family_ids = {info.id for info in list_by_family("Nintendo")}
    assert set(NINTENDO_PALETTE_IDS) <= family_ids
    assert "gameboy" in family_ids


def test_nintendo_profiles_are_data_driven() -> None:
    registered = {profile.id for profile in iter_platform_profiles()}
    for profile_id, palette_id in NINTENDO_PROFILE_PALETTES.items():
        profile = get_platform_profile(profile_id)
        assert profile_id in registered
        assert profile.family == "Nintendo"
        assert profile.manufacturer == "Nintendo"
        assert profile.platform
        assert profile.platform_family
        assert profile.generation
        assert profile.year >= 1983
        assert profile.color_count == EXPECTED_COLOR_COUNTS[palette_id]
        assert profile.palette_ids == (palette_id,)
        assert profile.default_palette_id == palette_id
        assert profile.tags
        assert profile.notes


def test_nes_and_15_bit_palette_caveats_are_documented() -> None:
    assert "emphasis" in get_palette_info("nes-default").notes.lower()
    assert "32,768" in get_palette_info("gameboy-color").notes
    assert "32,768" in get_palette_info("snes-default").notes
