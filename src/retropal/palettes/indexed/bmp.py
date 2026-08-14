"""Bounds-checked extraction of indexed BMP palette tables and pixel usage."""

from __future__ import annotations

import struct
from dataclasses import dataclass

from retropal.palettes.base import RGBColor
from retropal.palettes.indexed.base import IndexedPaletteError


@dataclass(frozen=True, slots=True)
class BmpStructure:
    colors: tuple[RGBColor, ...]
    width: int
    height: int
    used_indexes: set[int]
    dib_header: str
    nonzero_reserved_entries: bool


def _unpack_from(format_string: str, data: bytes, offset: int, label: str) -> tuple[int, ...]:
    size = struct.calcsize(format_string)
    if offset + size > len(data):
        raise IndexedPaletteError(f"Truncated BMP {label}")
    return struct.unpack_from(format_string, data, offset)


def extract_bmp_structure(data: bytes) -> BmpStructure:
    if len(data) < 18 or data[:2] != b"BM":
        raise IndexedPaletteError("Invalid or truncated BMP header")
    declared_size, pixel_offset = _unpack_from("<I4xI", data, 2, "file header")
    if declared_size != len(data):
        raise IndexedPaletteError("BMP declared file size does not match actual data")
    (dib_size,) = _unpack_from("<I", data, 14, "DIB header")
    if dib_size == 12:
        width, height, planes, bit_depth = _unpack_from("<HHHH", data, 18, "BITMAPCOREHEADER")
        color_count = 1 << bit_depth
        palette_offset = 26
        entry_size = 3
        dib_name = "BITMAPCOREHEADER"
        compression = 0
    elif dib_size in {40, 52, 56, 108, 124}:
        if 14 + dib_size > len(data):
            raise IndexedPaletteError("Truncated BMP DIB header")
        width, signed_height, planes, bit_depth, compression = _unpack_from(
            "<iiHHI", data, 18, "BITMAPINFOHEADER"
        )
        height = abs(signed_height)
        (colors_used,) = _unpack_from("<I", data, 46, "palette count")
        color_count = colors_used or 1 << bit_depth
        palette_offset = 14 + dib_size
        entry_size = 4
        dib_name = f"Windows DIB ({dib_size}-byte header)"
    else:
        raise IndexedPaletteError(f"Unsupported BMP DIB header size: {dib_size}")
    if width <= 0 or height <= 0 or planes != 1:
        raise IndexedPaletteError("Invalid BMP dimensions or plane count")
    if bit_depth not in {1, 4, 8}:
        raise IndexedPaletteError(f"BMP is not supported indexed 1/4/8-bit data: {bit_depth}-bit")
    if compression != 0:
        raise IndexedPaletteError("Compressed indexed BMP data is not supported")
    maximum_colors = 1 << bit_depth
    if not 1 <= color_count <= maximum_colors:
        raise IndexedPaletteError("BMP palette count is invalid for its bit depth")
    palette_end = palette_offset + color_count * entry_size
    if palette_end > len(data):
        raise IndexedPaletteError("Truncated BMP palette table")
    if pixel_offset < palette_end or pixel_offset > len(data):
        raise IndexedPaletteError("BMP pixel offset overlaps or exceeds the palette table")
    colors: list[RGBColor] = []
    nonzero_reserved = False
    for offset in range(palette_offset, palette_end, entry_size):
        blue, green, red = data[offset : offset + 3]
        colors.append((red, green, blue))
        if entry_size == 4 and data[offset + 3] != 0:
            nonzero_reserved = True
    row_stride = ((width * bit_depth + 31) // 32) * 4
    pixel_bytes = row_stride * height
    if pixel_offset + pixel_bytes > len(data):
        raise IndexedPaletteError("Truncated BMP pixel data")
    indexes: set[int] = set()
    for row_start in range(pixel_offset, pixel_offset + pixel_bytes, row_stride):
        row = data[row_start : row_start + row_stride]
        if bit_depth == 8:
            indexes.update(row[:width])
        elif bit_depth == 4:
            for x in range(width):
                value = row[x // 2]
                indexes.add(value >> 4 if x % 2 == 0 else value & 0x0F)
        else:
            for x in range(width):
                indexes.add((row[x // 8] >> (7 - x % 8)) & 1)
    return BmpStructure(tuple(colors), width, height, indexes, dib_name, nonzero_reserved)
