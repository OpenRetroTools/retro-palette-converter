"""Tests for the M2.3b Atari platform palette pack."""

from __future__ import annotations

from retropal import __version__
from retropal.palettes import (
    PALETTE_IDS,
    get_palette_info,
    list_by_family,
    list_by_manufacturer,
)
from retropal.palettes.fixed import load_fixed_palette

ATARI_PALETTE_IDS = (
    "atari-2600-tia",
    "atari-8bit-antic-gtia",
    "atari-st",
    "atari-ste",
    "atari-falcon030",
)

EXPECTED_COLOR_COUNTS = {
    "atari-2600-tia": 128,
    "atari-8bit-antic-gtia": 256,
    "atari-st": 16,
    "atari-ste": 16,
    "atari-falcon030": 256,
}


def test_atari_palettes_registered_in_registry() -> None:
    for palette_id in ATARI_PALETTE_IDS:
        assert palette_id in PALETTE_IDS


def test_atari_palette_ids_are_unique() -> None:
    assert len(set(PALETTE_IDS)) == len(PALETTE_IDS)


def test_atari_palettes_have_complete_metadata() -> None:
    for palette_id in ATARI_PALETTE_IDS:
        info = get_palette_info(palette_id)
        assert info.id == palette_id
        assert info.name
        assert info.family == "Atari"
        assert info.manufacturer == "Atari"
        assert info.year is not None
        assert info.color_count == EXPECTED_COLOR_COUNTS[palette_id]
        assert info.description
        assert not info.adaptive


def test_atari_palette_color_counts() -> None:
    for palette_id, expected in EXPECTED_COLOR_COUNTS.items():
        colors = load_fixed_palette(palette_id).colors
        assert len(colors) == expected


def test_atari_palette_rgb_values_are_valid() -> None:
    for palette_id in ATARI_PALETTE_IDS:
        colors = load_fixed_palette(palette_id).colors
        for color in colors:
            assert len(color) == 3
            for channel in color:
                assert isinstance(channel, int)
                assert 0 <= channel <= 255


def test_atari_family_filter_returns_all_five_platforms() -> None:
    family_ids = {info.id for info in list_by_family("Atari")}
    assert family_ids == set(ATARI_PALETTE_IDS)


def test_atari_family_filter_is_case_insensitive() -> None:
    assert {info.id for info in list_by_family("atari")} == set(ATARI_PALETTE_IDS)
    assert {info.id for info in list_by_family("ATARI")} == set(ATARI_PALETTE_IDS)


def test_atari_manufacturer_query() -> None:
    manufacturer_ids = {info.id for info in list_by_manufacturer("Atari")}
    assert manufacturer_ids >= set(ATARI_PALETTE_IDS)


def test_atari_palettes_are_discoverable_via_palette_ids_for_gui() -> None:
    # The GUI populates its palette combo boxes directly from PALETTE_IDS,
    # so registry membership is sufficient to guarantee GUI discoverability.
    for palette_id in ATARI_PALETTE_IDS:
        assert palette_id in PALETTE_IDS


def test_historical_accuracy_caveats_are_documented() -> None:
    # Palettes whose real hardware output varies by TV standard, revision,
    # emulator, or monitor must say so rather than claiming exactness.
    tia = get_palette_info("atari-2600-tia")
    assert "NTSC" in tia.description or "PAL" in tia.description

    gtia = get_palette_info("atari-8bit-antic-gtia")
    assert "representative" in gtia.description.lower()
    assert "no single canonical" in gtia.description.lower()

    st = get_palette_info("atari-st")
    assert "representative" in st.description.lower()
    assert "512" in st.description

    ste = get_palette_info("atari-ste")
    assert "representative" in ste.description.lower()
    assert "4096" in ste.description

    falcon = get_palette_info("atari-falcon030")
    assert "representative" in falcon.description.lower()
    assert "262,144" in falcon.description


def test_version_source_updated() -> None:
    assert __version__ == "0.2.0.dev2"
