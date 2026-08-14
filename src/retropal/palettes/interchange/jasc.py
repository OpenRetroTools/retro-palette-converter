"""JASC-PAL codec for version 0100."""

from __future__ import annotations

from retropal.palettes.custom import CustomPalette, CustomPaletteError
from retropal.palettes.interchange.base import (
    CodecInfo,
    ExportResult,
    ImportResult,
    InterchangeReport,
    PaletteCodecError,
    decode_text,
    metadata_loss,
)


class JascCodec:
    info = CodecInfo("jasc", "JASC-PAL", (".pal",), False, ("colors",))

    def sniff(self, data: bytes) -> bool:
        return data.startswith(b"JASC-PAL\r\n") or data.startswith(b"JASC-PAL\n")

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult:
        lines = decode_text(data, self.info.name).splitlines()
        if not lines or lines[0].strip() != "JASC-PAL":
            raise PaletteCodecError("Invalid JASC-PAL signature")
        if len(lines) < 3 or lines[1].strip() != "0100":
            version = lines[1].strip() if len(lines) > 1 else "missing"
            raise PaletteCodecError(f"Unsupported JASC-PAL version: {version}")
        try:
            count = int(lines[2].strip())
        except ValueError as exc:
            raise PaletteCodecError("Invalid JASC-PAL colour count") from exc
        if count <= 0:
            raise PaletteCodecError("JASC-PAL colour count must be positive")
        rows = [line for line in lines[3:] if line.strip()]
        if len(rows) != count:
            raise PaletteCodecError(f"JASC-PAL declares {count} colours but contains {len(rows)}")
        colors: list[tuple[int, int, int]] = []
        for line_number, row in enumerate(rows, start=4):
            fields = row.split()
            if len(fields) != 3:
                raise PaletteCodecError(f"Malformed JASC-PAL row {line_number}")
            try:
                color = tuple(int(field) for field in fields)
                validated = CustomPalette(
                    "validation", "Validation", ((color[0], color[1], color[2]),)
                )
            except (ValueError, CustomPaletteError) as exc:
                raise PaletteCodecError(
                    f"Invalid JASC-PAL RGB value on line {line_number}"
                ) from exc
            colors.append(validated.colors[0])
        palette = CustomPalette(
            palette_id, fallback_name, tuple(colors), source="Imported from JASC-PAL"
        )
        return ImportResult(palette, InterchangeReport(self.info.id))

    def encode(self, palette: CustomPalette) -> ExportResult:
        lines = ["JASC-PAL", "0100", str(len(palette.colors))]
        lines.extend(f"{red} {green} {blue}" for red, green, blue in palette.colors)
        return ExportResult(
            ("\r\n".join(lines) + "\r\n").encode(),
            InterchangeReport(self.info.id, metadata_loss(palette, self.info.preserves)),
        )


CODEC = JascCodec()
