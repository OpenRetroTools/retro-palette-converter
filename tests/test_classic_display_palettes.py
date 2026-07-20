"""Tests for the M2.3f classic computers and display standards pack."""

from __future__ import annotations

from retropal.palettes import PALETTE_IDS, get_palette_info
from retropal.palettes.fixed import load_fixed_palette
from retropal.palettes.profiles import get_platform_profile

CLASSIC_PALETTE_IDS = (
    "cga-palette-0",
    "cga-palette-1",
    "ega-default",
    "vga-16",
    "vga-256",
    "macintosh-bw",
    "macintosh-8bit",
    "hercules-default",
    "x68000-default",
)

PROFILE_PALETTES = {
    "ibm-pc-cga": ("cga-palette-0", "cga-palette-1"),
    "ibm-pc-ega": ("ega-default",),
    "ibm-pc-vga-16": ("vga-16",),
    "ibm-pc-vga-256": ("vga-256",),
    "apple-macintosh-bw": ("macintosh-bw",),
    "apple-macintosh-8bit": ("macintosh-8bit",),
    "hercules-monochrome": ("hercules-default",),
    "sharp-x68000": ("x68000-default",),
}

EXPECTED_COUNTS = {
    "cga-palette-0": 4,
    "cga-palette-1": 4,
    "ega-default": 16,
    "vga-16": 16,
    "vga-256": 256,
    "macintosh-bw": 2,
    "macintosh-8bit": 256,
    "hercules-default": 2,
    "x68000-default": 256,
}


def test_classic_palette_ids_load_with_expected_counts() -> None:
    assert set(CLASSIC_PALETTE_IDS) <= set(PALETTE_IDS)
    for palette_id, count in EXPECTED_COUNTS.items():
        palette = load_fixed_palette(palette_id)
        assert palette.id == palette_id
        assert len(palette.colors) == count


def test_classic_palette_representative_colours() -> None:
    assert load_fixed_palette("cga-palette-0").colors == (
        (0, 0, 0),
        (85, 255, 85),
        (255, 85, 85),
        (255, 255, 85),
    )
    assert (85, 255, 255) in load_fixed_palette("cga-palette-1").colors
    assert (170, 85, 0) in load_fixed_palette("ega-default").colors
    assert (255, 85, 255) in load_fixed_palette("vga-16").colors
    for palette_id in ("vga-256", "macintosh-8bit", "x68000-default"):
        colors = load_fixed_palette(palette_id).colors
        assert colors[0] == (0, 0, 0)
        assert (255, 0, 255) in colors
        assert colors[-1] == (255, 255, 255)
    assert set(load_fixed_palette("macintosh-bw").colors) == {
        (0, 0, 0),
        (255, 255, 255),
    }


def test_classic_palette_metadata() -> None:
    for palette_id in CLASSIC_PALETTE_IDS:
        info = get_palette_info(palette_id)
        assert info.manufacturer
        assert info.platform
        assert info.platform_family
        assert info.generation
        assert info.bit_depth
        assert info.palette_source
        assert info.color_count == EXPECTED_COUNTS[palette_id]
        assert info.notes
    assert get_palette_info("vga-256").dac_size == "18-bit DAC (6 bits per channel)"


def test_classic_profiles_filter_palettes() -> None:
    for profile_id, palette_ids in PROFILE_PALETTES.items():
        profile = get_platform_profile(profile_id)
        assert profile.palette_ids == palette_ids
        assert profile.default_palette_id == palette_ids[0]
        assert profile.color_count == EXPECTED_COUNTS[palette_ids[0]]
        assert profile.manufacturer
        assert profile.family
        assert profile.year
        assert profile.notes
        assert profile.tags


def test_hardware_emulation_exclusions_are_documented() -> None:
    assert "artifact" in get_palette_info("cga-palette-0").notes
    assert "DAC programming" in get_palette_info("vga-256").notes
    assert "QuickDraw" in get_palette_info("macintosh-8bit").notes
    assert "phosphor" in get_palette_info("hercules-default").notes
