from PIL import Image

from retropal.palettes import (
    PALETTE_IDS,
    get_palette_info,
    list_by_family,
    list_by_manufacturer,
    list_families,
    palette_colors,
)
from retropal.palettes.fixed import load_fixed_palette


def test_all_palettes_have_complete_metadata() -> None:
    for palette_id in PALETTE_IDS:
        info = get_palette_info(palette_id)
        assert info.id == palette_id
        assert info.name
        assert info.family
        assert info.manufacturer
        assert info.color_count > 0
        assert info.description


def test_commodore_pack_sizes() -> None:
    assert len(load_fixed_palette("commodore-64").colors) == 16
    assert len(load_fixed_palette("vic-20").colors) == 16
    assert len(load_fixed_palette("commodore-plus4").colors) == 121


def test_amiga_ecs_and_aga_are_adaptive() -> None:
    image = Image.new("RGB", (16, 16))
    image.putdata([(x, y, (x + y) % 256) for y in range(16) for x in range(16)])
    ecs = palette_colors("amiga-ecs-64", image)
    aga = palette_colors("amiga-aga-256", image)
    assert 1 <= len(ecs) <= 64
    assert all(channel % 17 == 0 for color in ecs for channel in color)
    assert 1 <= len(aga) <= 256


def test_metadata_queries() -> None:
    assert "Commodore" in list_families()
    assert {info.id for info in list_by_family("amiga")} >= {"amiga-ocs-16", "amiga-aga-256"}
    assert {info.id for info in list_by_manufacturer("commodore")} >= {"commodore-64", "vic-20"}
