"""Raw GIF color-table/GCE extraction for the first image frame."""

from __future__ import annotations

from dataclasses import dataclass

from retropal.palettes.base import RGBColor
from retropal.palettes.indexed.base import IndexedPaletteError
from retropal.palettes.indexed.pillow_usage import pillow_index_usage


@dataclass(frozen=True, slots=True)
class GifStructure:
    colors: tuple[RGBColor, ...]
    transparency_index: int | None
    frame_count: int
    distinct_frame_palettes: bool
    width: int
    height: int
    used_indexes: set[int]


def _read_color_table(data: bytes, offset: int, count: int) -> tuple[tuple[RGBColor, ...], int]:
    size = count * 3
    if offset + size > len(data):
        raise IndexedPaletteError("Truncated GIF color table")
    table = tuple(
        (data[index], data[index + 1], data[index + 2]) for index in range(offset, offset + size, 3)
    )
    return table, offset + size


def _skip_sub_blocks(data: bytes, offset: int, label: str) -> int:
    while True:
        if offset >= len(data):
            raise IndexedPaletteError(f"Truncated GIF {label} data")
        size = data[offset]
        offset += 1
        if size == 0:
            return offset
        if offset + size > len(data):
            raise IndexedPaletteError(f"Truncated GIF {label} sub-block")
        offset += size


def extract_gif_structure(data: bytes) -> GifStructure:
    if len(data) < 13 or data[:6] not in {b"GIF87a", b"GIF89a"}:
        raise IndexedPaletteError("Invalid or truncated GIF header")
    packed = data[10]
    global_table: tuple[RGBColor, ...] | None = None
    offset = 13
    if packed & 0x80:
        global_table, offset = _read_color_table(data, offset, 1 << ((packed & 0x07) + 1))
    pending_transparency: int | None = None
    frame_tables: list[tuple[RGBColor, ...]] = []
    first_transparency: int | None = None
    saw_trailer = False
    while offset < len(data):
        marker = data[offset]
        offset += 1
        if marker == 0x3B:
            saw_trailer = True
            break
        if marker == 0x21:
            if offset >= len(data):
                raise IndexedPaletteError("Truncated GIF extension")
            label = data[offset]
            offset += 1
            if label == 0xF9:
                if offset + 6 > len(data) or data[offset] != 4 or data[offset + 5] != 0:
                    raise IndexedPaletteError("Malformed GIF Graphic Control Extension")
                control = data[offset + 1 : offset + 5]
                pending_transparency = control[3] if control[0] & 0x01 else None
                offset += 6
            else:
                offset = _skip_sub_blocks(data, offset, "extension")
            continue
        if marker != 0x2C:
            raise IndexedPaletteError(f"Unexpected GIF block marker: 0x{marker:02X}")
        if offset + 9 > len(data):
            raise IndexedPaletteError("Truncated GIF image descriptor")
        descriptor = data[offset : offset + 9]
        offset += 9
        local_packed = descriptor[8]
        effective_table = global_table
        if local_packed & 0x80:
            effective_table, offset = _read_color_table(
                data, offset, 1 << ((local_packed & 0x07) + 1)
            )
        if effective_table is None:
            raise IndexedPaletteError("GIF frame has no global or local color table")
        if pending_transparency is not None and pending_transparency >= len(effective_table):
            raise IndexedPaletteError("GIF transparency index exceeds effective color table")
        frame_tables.append(effective_table)
        if len(frame_tables) == 1:
            first_transparency = pending_transparency
        pending_transparency = None
        if offset >= len(data):
            raise IndexedPaletteError("Truncated GIF image data")
        offset += 1  # LZW minimum code size
        offset = _skip_sub_blocks(data, offset, "image")
    if not saw_trailer or offset != len(data):
        raise IndexedPaletteError("GIF is missing trailer or contains trailing data")
    if not frame_tables:
        raise IndexedPaletteError("GIF contains no image frame")
    width, height, indexes = pillow_index_usage(data, "GIF")
    return GifStructure(
        frame_tables[0],
        first_transparency,
        len(frame_tables),
        any(table != frame_tables[0] for table in frame_tables[1:]),
        width,
        height,
        indexes,
    )
