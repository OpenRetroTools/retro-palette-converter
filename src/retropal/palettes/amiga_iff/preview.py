"""Narrow read-only indexed ILBM BODY decoding and palette rendering."""

from __future__ import annotations

import struct
from dataclasses import dataclass

from PIL import Image

from retropal.palettes.amiga_iff.base import IlbmDocument, IlbmPaletteError
from retropal.palettes.base import RGBColor

_HAM = 0x0800
_EHB = 0x0080


@dataclass(frozen=True, slots=True)
class IndexedIlbmImage:
    width: int
    height: int
    pixel_indexes: tuple[int, ...]
    mask: tuple[bool, ...] | None = None


def _decode_byterun_row(data: bytes, offset: int, expected: int) -> tuple[bytes, int]:
    output = bytearray()
    while len(output) < expected:
        if offset >= len(data):
            raise IlbmPaletteError("Truncated ByteRun1 BODY row")
        control = data[offset]
        offset += 1
        if control <= 127:
            count = control + 1
            if offset + count > len(data):
                raise IlbmPaletteError("Truncated ByteRun1 literal run")
            if len(output) + count > expected:
                raise IlbmPaletteError("ByteRun1 literal run exceeds row bounds")
            output.extend(data[offset : offset + count])
            offset += count
        elif control >= 129:
            count = 257 - control
            if offset >= len(data):
                raise IlbmPaletteError("Truncated ByteRun1 repeated run")
            if len(output) + count > expected:
                raise IlbmPaletteError("ByteRun1 repeated run exceeds row bounds")
            output.extend((data[offset],) * count)
            offset += 1
        # 128 is the documented no-op.
    return bytes(output), offset


def decode_byterun1_rows(data: bytes, row_size: int, row_count: int) -> bytes:
    """Decode independently bounded ByteRun1 rows, rejecting trailing data."""
    if row_size <= 0 or row_count < 0:
        raise IlbmPaletteError("Invalid ByteRun1 output dimensions")
    offset = 0
    rows: list[bytes] = []
    for _ in range(row_count):
        row, offset = _decode_byterun_row(data, offset, row_size)
        rows.append(row)
    if offset != len(data):
        raise IlbmPaletteError("ByteRun1 BODY contains trailing compressed data")
    return b"".join(rows)


def decode_indexed_ilbm(document: IlbmDocument) -> IndexedIlbmImage:
    bmhd_chunks = [chunk for chunk in document.chunks if chunk.id == b"BMHD"]
    body_chunks = [chunk for chunk in document.chunks if chunk.id == b"BODY"]
    if len(bmhd_chunks) != 1 or len(body_chunks) != 1:
        raise IlbmPaletteError("Indexed preview requires exactly one BMHD and BODY")
    payload = bmhd_chunks[0].payload
    if len(payload) != 20:
        raise IlbmPaletteError("BMHD must contain exactly 20 bytes")
    width, height, _x, _y, planes, masking, compression, _pad, transparent, *_rest = struct.unpack(
        ">HHhhBBBBHBBhh", payload
    )
    if not width or not height:
        raise IlbmPaletteError("ILBM preview dimensions must be non-zero")
    if not 1 <= planes <= 8:
        raise IlbmPaletteError(f"Unsupported indexed ILBM plane count: {planes}")
    if masking not in {0, 1, 2}:
        raise IlbmPaletteError(f"Unsupported ILBM masking mode: {masking}")
    if compression not in {0, 1}:
        raise IlbmPaletteError(f"Unsupported ILBM compression mode: {compression}")
    camg_chunks = [chunk for chunk in document.chunks if chunk.id == b"CAMG"]
    if camg_chunks:
        if len(camg_chunks[-1].payload) != 4:
            raise IlbmPaletteError("CAMG must contain exactly four bytes")
        mode = struct.unpack(">I", camg_chunks[-1].payload)[0]
        if mode & _HAM:
            raise IlbmPaletteError("HAM image preview is unsupported")
        if mode & _EHB:
            raise IlbmPaletteError("EHB image preview is unsupported")
    row_bytes = ((width + 15) // 16) * 2
    stored_planes = planes + (1 if masking == 1 else 0)
    row_count = height * stored_planes
    body = body_chunks[0].payload
    if compression == 1:
        decoded = decode_byterun1_rows(body, row_bytes, row_count)
    else:
        expected = row_bytes * row_count
        if len(body) != expected:
            raise IlbmPaletteError(
                f"Uncompressed BODY size mismatch: expected {expected}, got {len(body)}"
            )
        decoded = body
    indexes: list[int] = []
    mask_values: list[bool] | None = [] if masking in {1, 2} else None
    row_stride = row_bytes * stored_planes
    for y in range(height):
        row_start = y * row_stride
        for x in range(width):
            byte_index = x // 8
            bit = 7 - x % 8
            value = 0
            for plane in range(planes):
                plane_byte = decoded[row_start + plane * row_bytes + byte_index]
                value |= ((plane_byte >> bit) & 1) << plane
            indexes.append(value)
            if mask_values is not None:
                if masking == 1:
                    mask_byte = decoded[row_start + planes * row_bytes + byte_index]
                    mask_values.append(bool((mask_byte >> bit) & 1))
                else:
                    mask_values.append(value != transparent)
    return IndexedIlbmImage(
        width, height, tuple(indexes), tuple(mask_values) if mask_values else None
    )


def render_indexed_preview(indexed: IndexedIlbmImage, colors: tuple[RGBColor, ...]) -> Image.Image:
    pixels: list[tuple[int, int, int, int]] = []
    for position, palette_index in enumerate(indexed.pixel_indexes):
        if palette_index >= len(colors):
            raise IlbmPaletteError(
                f"Pixel index {palette_index} exceeds palette size {len(colors)}"
            )
        color = colors[palette_index]
        alpha = 255 if indexed.mask is None or indexed.mask[position] else 0
        pixels.append((*color, alpha))
    image = Image.new("RGBA", (indexed.width, indexed.height))
    image.putdata(pixels)
    return image
