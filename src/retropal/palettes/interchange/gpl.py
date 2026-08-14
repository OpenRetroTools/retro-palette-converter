"""GIMP GPL palette codec."""

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


class GplCodec:
    info = CodecInfo("gpl", "GIMP GPL", (".gpl",), False, ("name", "colors"))

    def sniff(self, data: bytes) -> bool:
        return data.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"GIMP Palette")

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult:
        lines = decode_text(data, self.info.name).splitlines()
        if not lines or lines[0].strip() != "GIMP Palette":
            raise PaletteCodecError("Invalid GIMP GPL header")
        name = fallback_name
        colors: list[tuple[int, int, int]] = []
        ignored_names = False
        for line_number, raw in enumerate(lines[1:], start=2):
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("Columns:"):
                continue
            if line.startswith("Name:"):
                candidate = line.removeprefix("Name:").strip()
                if not candidate:
                    raise PaletteCodecError(f"Empty GPL palette name on line {line_number}")
                name = candidate
                continue
            fields = line.split(maxsplit=3)
            if len(fields) < 3:
                raise PaletteCodecError(f"Malformed GPL colour on line {line_number}")
            try:
                color = tuple(int(field) for field in fields[:3])
                palette_color = (color[0], color[1], color[2])
                CustomPalette("validation", "Validation", (palette_color,))
            except (ValueError, CustomPaletteError) as exc:
                raise PaletteCodecError(f"Invalid GPL RGB value on line {line_number}") from exc
            colors.append(palette_color)
            ignored_names = ignored_names or len(fields) == 4
        if not colors:
            raise PaletteCodecError("GIMP GPL palette contains no colours")
        messages = (
            ("per-colour names are not represented by CustomPalette",) if ignored_names else ()
        )
        palette = CustomPalette(palette_id, name, tuple(colors), source="Imported from GIMP GPL")
        return ImportResult(palette, InterchangeReport(self.info.id, messages))

    def encode(self, palette: CustomPalette) -> ExportResult:
        lines = ["GIMP Palette", f"Name: {palette.name}", "Columns: 8", "#"]
        lines.extend(f"{red:3d} {green:3d} {blue:3d}" for red, green, blue in palette.colors)
        report = InterchangeReport(self.info.id, metadata_loss(palette, self.info.preserves))
        return ExportResult(("\n".join(lines) + "\n").encode(), report)


CODEC = GplCodec()
