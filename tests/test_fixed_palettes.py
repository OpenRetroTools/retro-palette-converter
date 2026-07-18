from retropal.palettes.fixed import fixed_palette_ids, load_fixed_palette


def test_all_fixed_palettes_load() -> None:
    for palette_id in fixed_palette_ids():
        palette = load_fixed_palette(palette_id)
        assert palette.id == palette_id
        assert palette.colors
        assert all(len(color) == 3 for color in palette.colors)


def test_expected_palette_sizes() -> None:
    assert len(load_fixed_palette("gameboy").colors) == 4
    assert len(load_fixed_palette("pico8").colors) == 16
    assert len(load_fixed_palette("ega").colors) == 16
    assert len(load_fixed_palette("dawnbringer16").colors) == 16
