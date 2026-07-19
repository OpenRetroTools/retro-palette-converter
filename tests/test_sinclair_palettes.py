"""Tests for the M2.3c Sinclair platform pack."""

from __future__ import annotations

from PIL import Image

from retropal.palettes import PALETTE_IDS, get_palette_info, list_by_family
from retropal.palettes.fixed import load_fixed_palette
from retropal.palettes.profiles import get_platform_profile, iter_platform_profiles

SINCLAIR_PALETTE_IDS = (
    "zx-spectrum-48k-normal",
    "zx-spectrum-48k-bright",
    "zx-spectrum-48k-auto",
    "zx-spectrum-128k-normal",
    "zx-spectrum-128k-bright",
    "zx-spectrum-128k-auto",
)


def test_sinclair_palettes_are_registered_and_loadable() -> None:
    assert set(SINCLAIR_PALETTE_IDS) <= set(PALETTE_IDS)
    for palette_id in SINCLAIR_PALETTE_IDS:
        palette = load_fixed_palette(palette_id)
        assert palette.id == palette_id
        assert palette.colors


def test_spectrum_normal_bright_and_auto_color_counts() -> None:
    for model in ("48k", "128k"):
        normal = load_fixed_palette(f"zx-spectrum-{model}-normal").colors
        bright = load_fixed_palette(f"zx-spectrum-{model}-bright").colors
        automatic = load_fixed_palette(f"zx-spectrum-{model}-auto").colors
        assert len(normal) == 8
        assert len(bright) == 8
        assert len(automatic) == 15
        assert set(automatic) == set(normal) | set(bright)


def test_spectrum_canonical_intensities() -> None:
    normal = load_fixed_palette("zx-spectrum-48k-normal").colors
    bright = load_fixed_palette("zx-spectrum-48k-bright").colors
    assert (0, 0, 205) in normal
    assert (205, 205, 205) in normal
    assert (0, 0, 255) in bright
    assert (255, 255, 255) in bright
    assert normal[0] == bright[0] == (0, 0, 0)


def test_sinclair_palette_metadata() -> None:
    expected_year = {"48k": 1982, "128k": 1985}
    for palette_id in SINCLAIR_PALETTE_IDS:
        model = "128k" if "128k" in palette_id else "48k"
        info = get_palette_info(palette_id)
        assert info.family == "Sinclair"
        assert info.manufacturer == "Sinclair Research"
        assert info.year == expected_year[model]
        assert info.platform == f"Sinclair ZX Spectrum {model.upper()}"
        assert info.notes
        assert {"sinclair", "zx-spectrum", model} <= set(info.tags)


def test_sinclair_family_lookup() -> None:
    assert {info.id for info in list_by_family("Sinclair")} == set(SINCLAIR_PALETTE_IDS)


def test_sinclair_platform_profile_lookup() -> None:
    profiles = {profile.id for profile in iter_platform_profiles()}
    for model in ("48k", "128k"):
        profile = get_platform_profile(f"sinclair-zx-spectrum-{model}")
        assert profile.id in profiles
        assert profile.family == "Sinclair"
        assert profile.default_palette_id == f"zx-spectrum-{model}-auto"
        assert set(profile.palette_ids) == {
            f"zx-spectrum-{model}-normal",
            f"zx-spectrum-{model}-bright",
            f"zx-spectrum-{model}-auto",
        }
        assert "attribute-cell" in profile.notes


def test_automatic_bright_conversion_can_use_both_intensities() -> None:
    from retropal.core.converter import convert

    image = Image.new("RGB", (2, 1))
    image.putdata([(0, 0, 210), (0, 0, 250)])
    converted = convert(image, "zx-spectrum-48k-auto")
    assert [pixel[:3] for pixel in converted.get_flattened_data()] == [
        (0, 0, 205),
        (0, 0, 255),
    ]
