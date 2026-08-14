"""Microsoft simple RIFF PAL codec.

Based on Microsoft's RIFF chunk rules and Multimedia Programming Interface
definition: RIFF('PAL ' data(<LOGPALETTE>)). LOGPALETTE and PALETTEENTRY are
decoded field-by-field with explicit little-endian widths; C struct padding is
never assumed.
"""

from __future__ import annotations

import struct

from retropal.palettes.custom import CustomPalette
from retropal.palettes.interchange.base import (
    CodecInfo,
    ExportResult,
    ImportResult,
    InterchangeReport,
    PaletteCodecError,
    metadata_loss,
)

_VERSION = 0x0300


class RiffPalCodec:
    info = CodecInfo(
        "riff-pal",
        "Microsoft RIFF PAL",
        (".pal",),
        True,
        ("colors",),
        maximum_colors=65535,
    )

    def sniff(self, data: bytes) -> bool:
        return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"PAL "

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult:
        if len(data) < 12 or data[:4] != b"RIFF":
            raise PaletteCodecError("Invalid RIFF signature")
        declared_size = struct.unpack_from("<I", data, 4)[0]
        if declared_size != len(data) - 8:
            raise PaletteCodecError(
                f"RIFF size mismatch: header declares {declared_size}, "
                f"file contains {len(data) - 8}"
            )
        if data[8:12] != b"PAL ":
            raise PaletteCodecError("RIFF form type is not PAL")
        offset = 12
        palette_data: bytes | None = None
        while offset < len(data):
            if len(data) - offset < 8:
                raise PaletteCodecError("Truncated RIFF chunk header")
            chunk_id = data[offset : offset + 4]
            chunk_size = struct.unpack_from("<I", data, offset + 4)[0]
            start = offset + 8
            end = start + chunk_size
            if end > len(data):
                raise PaletteCodecError(f"Truncated RIFF {chunk_id!r} chunk")
            if chunk_id != b"data":
                raise PaletteCodecError(f"Unsupported RIFF PAL chunk: {chunk_id!r}")
            if palette_data is not None:
                raise PaletteCodecError("RIFF PAL contains multiple data chunks")
            palette_data = data[start:end]
            offset = end + (chunk_size & 1)
            if offset > len(data):
                raise PaletteCodecError("Missing RIFF word-alignment padding")
        if palette_data is None:
            raise PaletteCodecError("RIFF PAL does not contain a data chunk")
        if len(palette_data) < 4:
            raise PaletteCodecError("Truncated RIFF LOGPALETTE header")
        version, count = struct.unpack_from("<HH", palette_data, 0)
        if version != _VERSION:
            raise PaletteCodecError(f"Unsupported RIFF PAL version: 0x{version:04X}")
        expected = 4 + count * 4
        if len(palette_data) != expected:
            raise PaletteCodecError(
                f"RIFF PAL entry count requires {expected} data bytes, found {len(palette_data)}"
            )
        if count == 0:
            raise PaletteCodecError("RIFF PAL contains no colours")
        colors = tuple(
            (palette_data[index], palette_data[index + 1], palette_data[index + 2])
            for index in range(4, expected, 4)
        )
        flags = palette_data[7:expected:4]
        messages = (
            ("PALETTEENTRY usage flags are not represented by CustomPalette",) if any(flags) else ()
        )
        palette = CustomPalette(
            palette_id, fallback_name, colors, source="Imported from Microsoft RIFF PAL"
        )
        return ImportResult(palette, InterchangeReport(self.info.id, messages))

    def encode(self, palette: CustomPalette) -> ExportResult:
        if len(palette.colors) > 0xFFFF:
            raise PaletteCodecError("RIFF PAL supports at most 65535 colours")
        body = bytearray(struct.pack("<HH", _VERSION, len(palette.colors)))
        for red, green, blue in palette.colors:
            body.extend((red, green, blue, 0))
        chunk = b"data" + struct.pack("<I", len(body)) + body
        riff_body = b"PAL " + chunk
        data = b"RIFF" + struct.pack("<I", len(riff_body)) + riff_body
        return ExportResult(
            data,
            InterchangeReport(self.info.id, metadata_loss(palette, self.info.preserves)),
        )


CODEC = RiffPalCodec()
