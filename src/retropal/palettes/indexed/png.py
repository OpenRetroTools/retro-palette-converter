"""Raw PNG PLTE/tRNS extraction with Pillow used only for pixel indexes."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass

from retropal.palettes.base import RGBColor
from retropal.palettes.indexed.base import IndexedPaletteError
from retropal.palettes.indexed.pillow_usage import pillow_index_usage

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True, slots=True)
class PngStructure:
    colors: tuple[RGBColor, ...]
    alpha: tuple[int, ...] | None
    width: int
    height: int
    used_indexes: set[int]


def extract_png_structure(data: bytes) -> PngStructure:
    if not data.startswith(PNG_SIGNATURE):
        raise IndexedPaletteError("Invalid PNG signature")
    offset = len(PNG_SIGNATURE)
    bit_depth: int | None = None
    color_type: int | None = None
    colors: tuple[RGBColor, ...] | None = None
    transparency: tuple[int, ...] | None = None
    saw_ihdr = False
    saw_idat = False
    saw_iend = False
    while offset < len(data):
        if len(data) - offset < 12:
            raise IndexedPaletteError("Truncated PNG chunk header")
        length = struct.unpack_from(">I", data, offset)[0]
        chunk_type = data[offset + 4 : offset + 8]
        start = offset + 8
        end = start + length
        crc_end = end + 4
        if crc_end > len(data):
            raise IndexedPaletteError(f"Truncated PNG {chunk_type!r} chunk")
        expected_crc = struct.unpack_from(">I", data, end)[0]
        actual_crc = zlib.crc32(chunk_type + data[start:end]) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise IndexedPaletteError(f"Invalid PNG {chunk_type!r} chunk CRC")
        payload = data[start:end]
        if not saw_ihdr and chunk_type != b"IHDR":
            raise IndexedPaletteError("PNG IHDR must be the first chunk")
        if chunk_type == b"IHDR":
            if saw_ihdr or length != 13:
                raise IndexedPaletteError("Invalid PNG IHDR chunk")
            saw_ihdr = True
            bit_depth = payload[8]
            color_type = payload[9]
            if color_type != 3:
                raise IndexedPaletteError("PNG image is not palette-indexed")
            if bit_depth not in {1, 2, 4, 8}:
                raise IndexedPaletteError(f"Unsupported indexed PNG bit depth: {bit_depth}")
        elif chunk_type == b"PLTE":
            if not saw_ihdr or saw_idat or colors is not None or length == 0 or length % 3:
                raise IndexedPaletteError("Invalid PNG PLTE chunk")
            if length > 768:
                raise IndexedPaletteError("PNG PLTE contains more than 256 entries")
            colors = tuple(
                (payload[index], payload[index + 1], payload[index + 2])
                for index in range(0, length, 3)
            )
        elif chunk_type == b"tRNS":
            if colors is None or saw_idat or transparency is not None:
                raise IndexedPaletteError("PNG tRNS must follow exactly one PLTE chunk")
            if length > len(colors):
                raise IndexedPaletteError("PNG tRNS has more entries than PLTE")
            transparency = tuple(payload) + (255,) * (len(colors) - length)
        elif chunk_type == b"IDAT":
            saw_idat = True
        elif chunk_type == b"IEND":
            if length != 0:
                raise IndexedPaletteError("Invalid PNG IEND chunk")
            saw_iend = True
            offset = crc_end
            break
        offset = crc_end
    if not saw_ihdr or colors is None:
        raise IndexedPaletteError("Indexed PNG is missing IHDR or PLTE")
    if bit_depth is None or len(colors) > 1 << bit_depth:
        raise IndexedPaletteError("PNG PLTE entry count exceeds indexed bit depth")
    if not saw_idat or not saw_iend or offset != len(data):
        raise IndexedPaletteError("PNG is missing image data/IEND or contains trailing data")
    width, height, indexes = pillow_index_usage(data, "PNG")
    return PngStructure(colors, transparency, width, height, indexes)
