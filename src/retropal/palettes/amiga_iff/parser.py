"""Narrow, bounds-checked EA IFF FORM/ILBM parser and serializer."""

from __future__ import annotations

import struct
from pathlib import Path

from retropal.palettes.amiga_iff.base import (
    ColorCycleRange,
    IffChunk,
    IlbmDocument,
    IlbmPaletteError,
)
from retropal.palettes.custom import CustomPalette


def _parse_crng(payload: bytes) -> ColorCycleRange:
    # Commodore ILBM: WORD pad1, WORD rate, WORD flags/active, UBYTE low, high.
    if len(payload) != 8:
        raise IlbmPaletteError(f"CRNG chunk must contain exactly 8 bytes, got {len(payload)}")
    reserved, rate, flags, low, high = struct.unpack(">HHHBB", payload)
    return ColorCycleRange(rate, flags, low, high, reserved, payload)


def parse_ilbm(
    data: bytes,
    *,
    palette_id: str = "ilbm-palette",
    palette_name: str = "ILBM Palette",
    source: str | None = None,
) -> IlbmDocument:
    """Parse one complete FORM ILBM without decoding its BODY."""
    if len(data) < 12:
        raise IlbmPaletteError("Truncated IFF FORM header")
    if data[:4] != b"FORM":
        raise IlbmPaletteError("Invalid IFF FORM signature")
    form_size = struct.unpack_from(">I", data, 4)[0]
    if form_size < 4 or form_size + 8 != len(data):
        raise IlbmPaletteError("IFF FORM size does not match file length")
    if data[8:12] != b"ILBM":
        raise IlbmPaletteError(f"Unsupported IFF FORM type: {data[8:12]!r}")
    chunks: list[IffChunk] = []
    offset = 12
    while offset < len(data):
        if offset + 8 > len(data):
            raise IlbmPaletteError("Truncated IFF chunk header")
        chunk_id = data[offset : offset + 4]
        chunk_size = struct.unpack_from(">I", data, offset + 4)[0]
        payload_start = offset + 8
        payload_end = payload_start + chunk_size
        padded_end = payload_end + (chunk_size & 1)
        if payload_end > len(data):
            raise IlbmPaletteError(f"IFF {chunk_id!r} chunk exceeds FORM bounds")
        if padded_end > len(data):
            raise IlbmPaletteError(f"IFF {chunk_id!r} chunk is missing its odd-length pad byte")
        pad = data[payload_end:padded_end]
        chunks.append(IffChunk(chunk_id, data[payload_start:payload_end], pad))
        offset = padded_end
    body_index = next(
        (index for index, chunk in enumerate(chunks) if chunk.id == b"BODY"), len(chunks)
    )
    for index, chunk in enumerate(chunks):
        if index > body_index and chunk.id in {b"CMAP", b"CRNG"}:
            raise IlbmPaletteError(f"{chunk.id.decode()} chunk appears after BODY")
    cmap_indexes = [index for index, chunk in enumerate(chunks[:body_index]) if chunk.id == b"CMAP"]
    for index in cmap_indexes:
        payload = chunks[index].payload
        if not payload or len(payload) % 3:
            raise IlbmPaletteError("CMAP payload must contain one or more complete RGB triples")
    effective_cmap_index = cmap_indexes[-1] if cmap_indexes else None
    palette: CustomPalette | None = None
    if effective_cmap_index is not None:
        payload = chunks[effective_cmap_index].payload
        colors = tuple(
            (payload[index], payload[index + 1], payload[index + 2])
            for index in range(0, len(payload), 3)
        )
        palette = CustomPalette(palette_id, palette_name, colors, source=source)
    cycles = tuple(_parse_crng(chunk.payload) for chunk in chunks if chunk.id == b"CRNG")
    return IlbmDocument(b"ILBM", tuple(chunks), palette, cycles, effective_cmap_index, source)


def serialize_ilbm(document: IlbmDocument) -> bytes:
    """Serialize ordered chunks, retaining original payloads and pad bytes."""
    encoded_chunks: list[bytes] = []
    for chunk in document.chunks:
        encoded_chunks.append(
            chunk.id + struct.pack(">I", len(chunk.payload)) + chunk.payload + chunk.pad_byte
        )
    if document.form_type != b"ILBM":
        raise IlbmPaletteError(f"Unsupported IFF FORM type: {document.form_type!r}")
    contents = document.form_type + b"".join(encoded_chunks)
    return b"FORM" + struct.pack(">I", len(contents)) + contents


def load_ilbm_document(path: Path, *, palette_id: str, palette_name: str) -> IlbmDocument:
    return parse_ilbm(
        path.read_bytes(),
        palette_id=palette_id,
        palette_name=palette_name,
        source=f"CMAP imported from ILBM {path.name}",
    )
