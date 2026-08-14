from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from PIL import Image

from retropal.core.converter import convert
from retropal.palettes import palette_colors
from retropal.palettes.base import RGBColor
from retropal.palettes.custom import CustomPalette, CustomPaletteError
from retropal.palettes.native import (
    NATIVE_SCHEMA,
    NATIVE_SCHEMA_VERSION,
    NativePaletteError,
    load_native_palette,
    save_native_palette,
)
from retropal.palettes.store import CustomPaletteStore


def test_custom_palette_preserves_order_and_duplicates() -> None:
    colors = ((12, 34, 56), (255, 0, 0), (12, 34, 56), (0, 0, 0))
    palette = CustomPalette("ordered-demo", "Ordered Demo", colors)

    assert palette.colors == colors
    assert palette.colors[0] == palette.colors[2]


@pytest.mark.parametrize(
    "palette_id",
    ["", "UPPER", "two words", "leading-", "-leading", "two--hyphens", "1starts-number"],
)
def test_custom_palette_rejects_invalid_ids(palette_id: str) -> None:
    with pytest.raises(CustomPaletteError, match="Palette ID"):
        CustomPalette(palette_id, "Name", ((0, 0, 0),))


@pytest.mark.parametrize(
    "color",
    [(-1, 0, 0), (256, 0, 0), (1.5, 0, 0), (True, 0, 0), (0, 0), (0, 0, 0, 0)],
)
def test_custom_palette_rejects_invalid_rgb(color: tuple[object, ...]) -> None:
    with pytest.raises(CustomPaletteError, match="Invalid RGB"):
        CustomPalette("invalid-rgb", "Invalid", cast(tuple[RGBColor, ...], (color,)))


def test_custom_palette_rejects_empty_name_and_colors() -> None:
    with pytest.raises(CustomPaletteError, match="name"):
        CustomPalette("empty-name", " ", ((0, 0, 0),))
    with pytest.raises(CustomPaletteError, match="at least one"):
        CustomPalette("empty-colors", "Empty", ())


def test_custom_palette_edit_operations_are_immutable_and_indexed() -> None:
    original = CustomPalette("editing", "Editing", ((0, 0, 0), (10, 20, 30)))
    edited = original.rename("Renamed").add_color((40, 50, 60), 1)
    edited = edited.set_color(0, (1, 2, 3)).move_color(2, 0).remove_color(1)

    assert original.name == "Editing"
    assert original.colors == ((0, 0, 0), (10, 20, 30))
    assert edited.name == "Renamed"
    assert edited.colors == ((10, 20, 30), (40, 50, 60))


def test_custom_palette_rejects_invalid_edit_operations() -> None:
    palette = CustomPalette("editing", "Editing", ((0, 0, 0),))
    with pytest.raises(CustomPaletteError, match="insertion index"):
        palette.add_color((1, 2, 3), 2)
    with pytest.raises(CustomPaletteError, match="index out of range"):
        palette.set_color(2, (1, 2, 3))
    with pytest.raises(CustomPaletteError, match="at least one"):
        palette.remove_color(0)
    with pytest.raises(CustomPaletteError, match="Target"):
        palette.move_color(0, 1)


def test_native_round_trip_preserves_identity_order_duplicates_and_metadata(tmp_path: Path) -> None:
    original = CustomPalette(
        "round-trip",
        "Initial Name",
        ((1, 2, 3), (40, 50, 60), (1, 2, 3)),
        "A palette description",
        "hand-authored",
    )
    edited = original.rename("Finished Palette").add_color((70, 80, 90), 1)
    edited = edited.set_color(2, (100, 110, 120)).move_color(3, 0)
    path = tmp_path / "palette.retropal-palette.json"

    save_native_palette(edited, path)
    loaded = load_native_palette(path)

    assert loaded == edited
    assert loaded.colors == (
        (1, 2, 3),
        (1, 2, 3),
        (70, 80, 90),
        (100, 110, 120),
    )
    assert loaded.description == "A palette description"
    assert loaded.source == "hand-authored"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == NATIVE_SCHEMA
    assert payload["version"] == NATIVE_SCHEMA_VERSION


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("not-json", "Malformed native palette JSON"),
        (json.dumps([]), "must be a JSON object"),
        (json.dumps({"schema": "other", "version": 1}), "Unsupported native palette schema"),
        (
            json.dumps({"schema": NATIVE_SCHEMA, "version": 99, "palette": {}}),
            "Unsupported native palette version",
        ),
        (
            json.dumps({"schema": NATIVE_SCHEMA, "version": 1, "palette": {}}),
            "Invalid native palette fields",
        ),
    ],
)
def test_native_loader_reports_controlled_errors(
    tmp_path: Path, payload: str, message: str
) -> None:
    path = tmp_path / "bad.retropal-palette.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(NativePaletteError, match=message):
        load_native_palette(path)


def test_store_separates_custom_palettes_and_rejects_duplicate_ids(tmp_path: Path) -> None:
    store = CustomPaletteStore(tmp_path)
    custom = store.create("my-palette", "Mine", ((1, 2, 3),))

    assert store.get("my-palette") is custom
    assert palette_colors("gameboy", Image.new("RGBA", (1, 1)))
    with pytest.raises(CustomPaletteError, match="Duplicate custom"):
        store.add(custom)
    with pytest.raises(CustomPaletteError, match="reserved by a built-in"):
        store.create("gameboy", "Collision", ((0, 0, 0),))


def test_store_save_load_and_delete_lifecycle(tmp_path: Path) -> None:
    first = CustomPaletteStore(tmp_path)
    palette = first.create("stored", "Stored", ((9, 8, 7), (9, 8, 7)))
    path = first.save(palette.id)

    second = CustomPaletteStore(tmp_path)
    assert second.load_all() == (palette,)
    second.delete(palette.id)

    assert not path.exists()
    with pytest.raises(CustomPaletteError, match="Unknown custom"):
        second.get(palette.id)


def test_store_rejects_duplicate_ids_across_native_files(tmp_path: Path) -> None:
    palette = CustomPalette("duplicate-file", "Duplicate", ((1, 2, 3),))
    save_native_palette(palette, tmp_path / "first.retropal-palette.json")
    save_native_palette(palette, tmp_path / "second.retropal-palette.json")

    with pytest.raises(CustomPaletteError, match="Duplicate custom palette ID"):
        CustomPaletteStore(tmp_path).load_all()


def test_store_exposes_filesystem_errors_without_losing_palette(tmp_path: Path) -> None:
    blocked_directory = tmp_path / "not-a-directory"
    blocked_directory.write_text("occupied", encoding="utf-8")
    store = CustomPaletteStore(blocked_directory)
    palette = store.create("filesystem", "Filesystem", ((1, 2, 3),))

    with pytest.raises(OSError):
        store.save(palette.id)

    assert store.get(palette.id) == palette


@pytest.mark.parametrize("dither", ["none", "floyd-steinberg", "bayer-4x4"])
def test_custom_palette_uses_existing_conversion_pipeline(dither: str) -> None:
    palette = CustomPalette("conversion", "Conversion", ((0, 0, 0), (255, 255, 255)))
    image = Image.new("RGBA", (4, 2), (128, 128, 128, 120))

    result = convert(image, palette.id, dither, colors=palette.colors)

    assert result.mode == "RGBA"
    assert result.size == image.size
    assert {pixel[:3] for pixel in result.get_flattened_data()} <= set(palette.colors)
    assert {pixel[3] for pixel in result.get_flattened_data()} == {120}
