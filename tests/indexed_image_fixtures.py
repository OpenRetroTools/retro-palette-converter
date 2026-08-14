"""Tiny byte-level indexed-image fixtures, constructed independently of Pillow."""

from __future__ import annotations

import struct
import zlib


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def indexed_png(
    colors: tuple[tuple[int, int, int], ...],
    indexes: bytes = b"\x01\x01",
    transparency: bytes | None = None,
) -> bytes:
    ihdr = struct.pack(">IIBBBBB", len(indexes), 1, 8, 3, 0, 0, 0)
    plte = bytes(channel for color in colors for channel in color)
    chunks = [_png_chunk(b"IHDR", ihdr), _png_chunk(b"PLTE", plte)]
    if transparency is not None:
        chunks.append(_png_chunk(b"tRNS", transparency))
    chunks.extend((_png_chunk(b"IDAT", zlib.compress(b"\x00" + indexes)), _png_chunk(b"IEND", b"")))
    return b"\x89PNG\r\n\x1a\n" + b"".join(chunks)


def indexed_gif(
    colors: tuple[tuple[int, int, int], ...],
    *,
    transparency_index: int | None = None,
    local_colors: tuple[tuple[int, int, int], ...] | None = None,
    second_local_colors: tuple[tuple[int, int, int], ...] | None = None,
) -> bytes:
    if len(colors) not in {2, 4, 8, 16, 32, 64, 128, 256}:
        raise ValueError("GIF fixture tables must have a power-of-two size")
    size_code = len(colors).bit_length() - 2
    header = b"GIF89a" + struct.pack("<HHBBB", 1, 1, 0x80 | size_code, 0, 0)
    table = bytes(channel for color in colors for channel in color)
    gce = (
        b"\x21\xf9\x04\x01\x00\x00" + bytes((transparency_index,)) + b"\x00"
        if transparency_index is not None
        else b""
    )

    def frame(frame_colors: tuple[tuple[int, int, int], ...] | None) -> bytes:
        packed = 0
        local = b""
        if frame_colors is not None:
            packed = 0x80 | (len(frame_colors).bit_length() - 2)
            local = bytes(channel for color in frame_colors for channel in color)
        descriptor = b"\x2c" + struct.pack("<HHHHB", 0, 0, 1, 1, packed)
        # LZW clear, palette index 0, end code for a two-bit minimum code size.
        return descriptor + local + b"\x02\x02\x44\x01\x00"

    frames = frame(local_colors)
    if second_local_colors is not None:
        frames += frame(second_local_colors)
    return header + table + gce + frames + b"\x3b"


def indexed_bmp(
    bit_depth: int,
    colors: tuple[tuple[int, int, int], ...],
    indexes: tuple[int, ...],
    *,
    core_header: bool = False,
) -> bytes:
    width, height = len(indexes), 1
    stride = ((width * bit_depth + 31) // 32) * 4
    if bit_depth == 8:
        row = bytes(indexes)
    elif bit_depth == 4:
        row = bytes(
            (indexes[index] << 4) | (indexes[index + 1] if index + 1 < width else 0)
            for index in range(0, width, 2)
        )
    else:
        value = sum(index << (7 - position) for position, index in enumerate(indexes))
        row = bytes((value,))
    pixels = row + bytes(stride - len(row))
    if core_header:
        dib = struct.pack("<IHHHH", 12, width, height, 1, bit_depth)
        palette = bytes(channel for red, green, blue in colors for channel in (blue, green, red))
    else:
        dib = struct.pack(
            "<IiiHHIIiiII", 40, width, height, 1, bit_depth, 0, len(pixels), 0, 0, len(colors), 0
        )
        palette = bytes(channel for red, green, blue in colors for channel in (blue, green, red, 0))
    pixel_offset = 14 + len(dib) + len(palette)
    size = pixel_offset + len(pixels)
    return b"BM" + struct.pack("<IHHI", size, 0, 0, pixel_offset) + dib + palette + pixels
