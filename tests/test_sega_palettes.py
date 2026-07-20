"""Tests for the M2.3e Sega platform pack."""

from __future__ import annotations

from retropal.palettes import PALETTE_IDS, get_palette_info, list_by_family
from retropal.palettes.fixed import load_fixed_palette
from retropal.palettes.profiles import get_platform_profile, iter_platform_profiles

SEGA_PALETTE_IDS = (
    "master-system-default",
    "game-gear-default",
    "megadrive-default",
)

SEGA_PROFILE_PALETTES = {
    "sega-master-system": "master-system-default",
    "sega-game-gear": "game-gear-default",
    "sega-megadrive": "megadrive-default",
}

EXPECTED_COLOR_COUNTS = {
    "master-system-default": 64,
    "game-gear-default": 4096,
    "megadrive-default": 512,
}


def test_sega_palette_ids_are_registered_and_loadable() -> None:
    assert set(SEGA_PALETTE_IDS) <= set(PALETTE_IDS)
    for palette_id in SEGA_PALETTE_IDS:
        palette = load_fixed_palette(palette_id)
        assert palette.id == palette_id
        assert len(palette.colors) == EXPECTED_COLOR_COUNTS[palette_id]


def test_sega_rgb_spaces_are_complete_and_deterministic() -> None:
    expected_levels = {
        "master-system-default": (0, 85, 170, 255),
        "game-gear-default": tuple(range(0, 256, 17)),
        "megadrive-default": (0, 36, 73, 109, 146, 182, 219, 255),
    }
    for palette_id, levels in expected_levels.items():
        colors = load_fixed_palette(palette_id).colors
        assert colors[0] == (0, 0, 0)
        assert colors[-1] == (255, 255, 255)
        assert {channel for color in colors for channel in color} == set(levels)
        assert len(set(colors)) == len(levels) ** 3


def test_sega_palette_metadata() -> None:
    for palette_id in SEGA_PALETTE_IDS:
        info = get_palette_info(palette_id)
        assert info.family == "Sega"
        assert info.manufacturer == "Sega"
        assert info.platform
        assert info.platform_family in {"Sega home console", "Sega handheld"}
        assert info.generation
        assert info.year is not None
        assert info.color_count == EXPECTED_COLOR_COUNTS[palette_id]
        assert "sega" in info.tags
        assert "not emulated" in info.notes


def test_sega_family_lookup() -> None:
    assert {info.id for info in list_by_family("Sega")} == set(SEGA_PALETTE_IDS)


def test_sega_profiles_are_data_driven() -> None:
    registered = {profile.id for profile in iter_platform_profiles()}
    for profile_id, palette_id in SEGA_PROFILE_PALETTES.items():
        profile = get_platform_profile(profile_id)
        assert profile_id in registered
        assert profile.family == "Sega"
        assert profile.manufacturer == "Sega"
        assert profile.platform
        assert profile.platform_family
        assert profile.generation
        assert profile.color_count == EXPECTED_COLOR_COUNTS[palette_id]
        assert profile.palette_ids == (palette_id,)
        assert profile.default_palette_id == palette_id
        assert profile.tags
        assert profile.notes


def test_sega_hardware_exclusions_are_documented() -> None:
    assert "CRAM" in get_palette_info("master-system-default").notes
    assert "LCD" in get_palette_info("game-gear-default").notes
    megadrive_notes = get_palette_info("megadrive-default").notes
    assert "shadow/highlight" in megadrive_notes
    assert "animation" in megadrive_notes
