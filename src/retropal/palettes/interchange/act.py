"""Adobe Color Table codec for documented 768- and 772-byte forms.

Adobe specifies 256 consecutive RGB triples. The optional four-byte trailer is
two big-endian 16-bit values: used colour count and transparency index. This
codec writes the trailer only for palettes shorter than 256 entries and does
not map transparency into the RGB-only CustomPalette model.
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


class ActCodec:
    info = CodecInfo("act", "Adobe Color Table", (".act",), True, ("colors",))

    def sniff(self, data: bytes) -> bool:
        return len(data) in {768, 772}

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult:
        if len(data) not in {768, 772}:
            raise PaletteCodecError("Adobe ACT must be exactly 768 or 772 bytes")
        count = 256
        messages: tuple[str, ...] = ()
        if len(data) == 772:
            count, transparency = struct.unpack_from(">HH", data, 768)
            if not 1 <= count <= 256:
                raise PaletteCodecError(f"Invalid Adobe ACT colour count: {count}")
            if transparency != 0xFFFF:
                if transparency >= count:
                    raise PaletteCodecError(
                        f"Adobe ACT transparency index {transparency} exceeds colour count {count}"
                    )
                messages = ("transparency index is not represented by CustomPalette",)
        colors = tuple(
            (data[offset], data[offset + 1], data[offset + 2]) for offset in range(0, count * 3, 3)
        )
        palette = CustomPalette(
            palette_id,
            fallback_name,
            colors,
            source="Imported from Adobe Color Table",
        )
        return ImportResult(palette, InterchangeReport(self.info.id, messages))

    def encode(self, palette: CustomPalette) -> ExportResult:
        count = len(palette.colors)
        if count > 256:
            raise PaletteCodecError("Adobe ACT supports at most 256 colours")
        table = b"".join(bytes(color) for color in palette.colors)
        table += b"\x00" * (768 - len(table))
        if count < 256:
            table += struct.pack(">HH", count, 0xFFFF)
        return ExportResult(
            table,
            InterchangeReport(self.info.id, metadata_loss(palette, self.info.preserves)),
        )


CODEC = ActCodec()
