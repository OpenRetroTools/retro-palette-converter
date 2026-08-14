from __future__ import annotations

import struct
from pathlib import Path

import pytest
from PIL import Image

from retropal.core.converter import convert
from retropal.palettes.indexed import IndexedPaletteError, extract_indexed_palette
from retropal.palettes.native import load_native_palette
from retropal.palettes.store import CustomPaletteStore
from tests.indexed_image_fixtures import indexed_bmp, indexed_gif, indexed_png

COLORS = ((0, 0, 0), (255, 0, 0), (0, 0, 0), (0, 0, 255))


def _write(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def test_png_preserves_full_order_duplicates_unused_and_partial_trns(tmp_path: Path) -> None:
    result = extract_indexed_palette(
        _write(tmp_path / "My Indexed.png", indexed_png(COLORS, transparency=b"\x00\x80"))
    )
    assert result.palette.id == "my-indexed"
    assert result.palette.name == "My Indexed (PNG palette)"
    assert result.palette.colors == COLORS
    assert result.used_indexes == (1,)
    assert result.unused_indexes == (0, 2, 3)
    assert result.transparency is not None
    assert result.transparency.alpha_by_index == (0, 128, 255, 255)
    assert result.palette.source == "Indexed PNG palette extracted from My Indexed.png"
    assert "native custom palettes store RGB only" in result.messages[-1]


def test_png_rejects_nonindexed_and_malformed_chunks(tmp_path: Path) -> None:
    rgb = tmp_path / "rgb.png"
    Image.new("RGB", (1, 1)).save(rgb)
    with pytest.raises(IndexedPaletteError, match="not palette-indexed"):
        extract_indexed_palette(rgb)
    malformed = bytearray(indexed_png(COLORS))
    plte = malformed.index(b"PLTE")
    malformed[plte + 5] ^= 1
    with pytest.raises(IndexedPaletteError, match="CRC"):
        extract_indexed_palette(_write(tmp_path / "bad.png", bytes(malformed)))
    with pytest.raises(IndexedPaletteError, match="Truncated"):
        extract_indexed_palette(_write(tmp_path / "short.png", indexed_png(COLORS)[:-5]))
    excessive_trns = indexed_png(((0, 0, 0), (1, 1, 1)), transparency=b"\x00\x01\x02")
    with pytest.raises(IndexedPaletteError, match="more entries than PLTE"):
        extract_indexed_palette(_write(tmp_path / "alpha.png", excessive_trns))


def test_gif_global_table_transparency_and_unused_entries(tmp_path: Path) -> None:
    result = extract_indexed_palette(
        _write(tmp_path / "global.gif", indexed_gif(COLORS, transparency_index=2))
    )
    assert result.palette.colors == COLORS
    assert result.used_indexes == (0,)
    assert result.unused_indexes == (1, 2, 3)
    assert result.transparency is not None
    assert result.transparency.non_opaque_indexes == (2,)


def test_gif_first_frame_local_table_and_multiframe_warning(tmp_path: Path) -> None:
    local = ((1, 2, 3), (4, 5, 6), (1, 2, 3), (7, 8, 9))
    other = ((9, 8, 7), (6, 5, 4), (3, 2, 1), (0, 0, 0))
    result = extract_indexed_palette(
        _write(
            tmp_path / "animated.gif",
            indexed_gif(COLORS, local_colors=local, second_local_colors=other),
        )
    )
    assert result.palette.colors == local
    assert result.frame_index == 0
    assert result.frame_count == 2
    assert not result.all_stored_semantics_preserved
    assert any("different effective color tables" in message for message in result.messages)


def test_gif_rejects_missing_table_bad_control_and_truncation(tmp_path: Path) -> None:
    missing = b"GIF89a" + struct.pack("<HHBBB", 1, 1, 0, 0, 0) + indexed_gif(COLORS)[25:]
    with pytest.raises(IndexedPaletteError, match="no global or local"):
        extract_indexed_palette(_write(tmp_path / "missing.gif", missing))
    bad_control = indexed_gif(COLORS, transparency_index=0).replace(
        b"\x21\xf9\x04", b"\x21\xf9\x03"
    )
    with pytest.raises(IndexedPaletteError, match="Graphic Control"):
        extract_indexed_palette(_write(tmp_path / "control.gif", bad_control))
    with pytest.raises(IndexedPaletteError, match="Truncated|trailer"):
        extract_indexed_palette(_write(tmp_path / "short.gif", indexed_gif(COLORS)[:-3]))


@pytest.mark.parametrize(
    ("bit_depth", "colors", "indexes", "core"),
    [
        (1, ((0, 0, 0), (255, 255, 255)), (1, 0), True),
        (4, COLORS, (3, 1, 0), False),
        (8, COLORS, (1, 1), False),
    ],
)
def test_bmp_indexed_depths_palette_count_order_and_usage(
    tmp_path: Path,
    bit_depth: int,
    colors: tuple[tuple[int, int, int], ...],
    indexes: tuple[int, ...],
    core: bool,
) -> None:
    result = extract_indexed_palette(
        _write(
            tmp_path / f"depth-{bit_depth}.bmp",
            indexed_bmp(bit_depth, colors, indexes, core_header=core),
        )
    )
    assert result.palette.colors == colors
    assert result.used_indexes == tuple(sorted(set(indexes)))
    assert result.stored_entry_count == len(colors)


def test_bmp_rejects_truncated_palette_and_nonindexed_data(tmp_path: Path) -> None:
    data = indexed_bmp(8, COLORS, (1,))
    pixel_offset = struct.unpack_from("<I", data, 10)[0]
    truncated = data[: pixel_offset - 2]
    truncated = truncated[:2] + struct.pack("<I", len(truncated)) + truncated[6:]
    with pytest.raises(IndexedPaletteError, match="palette|offset"):
        extract_indexed_palette(_write(tmp_path / "short.bmp", truncated))
    rgb = tmp_path / "rgb.bmp"
    Image.new("RGB", (1, 1)).save(rgb)
    with pytest.raises(IndexedPaletteError, match="not supported indexed"):
        extract_indexed_palette(rgb)


def test_extracted_palette_native_save_and_conversion(tmp_path: Path) -> None:
    result = extract_indexed_palette(_write(tmp_path / "source.png", indexed_png(COLORS)))
    store = CustomPaletteStore(tmp_path / "store")
    store.add(result.palette)
    saved = store.save(result.palette.id)
    assert load_native_palette(saved) == result.palette
    source = Image.new("RGB", (2, 1), (240, 5, 5))
    output = convert(source, result.palette.id, colors=result.palette.colors)
    assert output.getpixel((0, 0))[:3] in result.palette.colors


def test_format_override_and_unknown_signature_are_controlled(tmp_path: Path) -> None:
    source = _write(tmp_path / "wrong.dat", indexed_png(COLORS))
    with pytest.raises(IndexedPaletteError, match="does not match"):
        extract_indexed_palette(source, format_id="gif")
    with pytest.raises(IndexedPaletteError, match="not a recognized"):
        extract_indexed_palette(_write(tmp_path / "unknown.dat", b"not an image"))
