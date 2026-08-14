"""Small hand-built IFF/ILBM byte fixtures independent of the production writer."""

from __future__ import annotations

import struct


def iff_chunk(chunk_id: bytes, payload: bytes, *, pad: bytes = b"\0") -> bytes:
    alignment = pad if len(payload) % 2 else b""
    return chunk_id + struct.pack(">I", len(payload)) + payload + alignment


def ilbm_form(*chunks: bytes, form_type: bytes = b"ILBM") -> bytes:
    body = form_type + b"".join(chunks)
    return b"FORM" + struct.pack(">I", len(body)) + body


def crng(rate: int, flags: int, low: int, high: int, reserved: int = 0) -> bytes:
    return struct.pack(">HHHBB", reserved, rate, flags, low, high)


def bmhd(
    width: int,
    height: int,
    planes: int,
    *,
    masking: int = 0,
    compression: int = 0,
    transparent: int = 0,
) -> bytes:
    return struct.pack(
        ">HHhhBBBBHBBhh",
        width,
        height,
        0,
        0,
        planes,
        masking,
        compression,
        0,
        transparent,
        1,
        1,
        width,
        height,
    )


def rich_ilbm() -> bytes:
    colors = bytes((1, 2, 3, 255, 0, 128, 1, 2, 3))
    return ilbm_form(
        iff_chunk(b"ANNO", b"odd", pad=b"\x7f"),
        iff_chunk(b"CRNG", crng(273, 1, 1, 3)),
        iff_chunk(b"BMHD", bytes(range(20))),
        iff_chunk(b"XXXX", b"unknown"),
        iff_chunk(b"CMAP", colors),
        iff_chunk(b"AUTH", b"RetroPal"),
        iff_chunk(b"CRNG", crng(8192, 3, 4, 7, reserved=0x1234)),
        iff_chunk(b"BODY", b"\xaa\xbb\xcc"),
    )
