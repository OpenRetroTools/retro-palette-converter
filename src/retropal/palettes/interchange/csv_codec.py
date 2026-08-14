"""Canonical UTF-8 CSV palette codec: index,r,g,b."""

from __future__ import annotations

import csv
import io

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

_HEADER = ["index", "r", "g", "b"]


class CsvCodec:
    info = CodecInfo("csv", "CSV palette", (".csv",), False, ("colors",))

    def sniff(self, data: bytes) -> bool:
        try:
            first = next(csv.reader(io.StringIO(data.decode("utf-8-sig")), strict=True))
        except (UnicodeDecodeError, StopIteration, csv.Error):
            return False
        return first == _HEADER

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult:
        try:
            rows = list(
                csv.reader(io.StringIO(decode_text(data, self.info.name), newline=""), strict=True)
            )
        except csv.Error as exc:
            raise PaletteCodecError(f"Malformed CSV palette: {exc}") from exc
        if not rows or rows[0] != _HEADER:
            raise PaletteCodecError("CSV palette header must be: index,r,g,b")
        colors: list[tuple[int, int, int]] = []
        for expected_index, row in enumerate(rows[1:]):
            if len(row) != 4:
                raise PaletteCodecError(f"CSV palette row {expected_index + 2} must have 4 columns")
            try:
                index, red, green, blue = (int(value) for value in row)
                color = CustomPalette("validation", "Validation", ((red, green, blue),)).colors[0]
            except (ValueError, CustomPaletteError) as exc:
                raise PaletteCodecError(f"Invalid CSV palette row {expected_index + 2}") from exc
            if index != expected_index:
                raise PaletteCodecError(
                    f"CSV palette index mismatch on row {expected_index + 2}: "
                    f"expected {expected_index}, found {index}"
                )
            colors.append(color)
        if not colors:
            raise PaletteCodecError("CSV palette contains no colours")
        palette = CustomPalette(
            palette_id, fallback_name, tuple(colors), source="Imported from CSV"
        )
        return ImportResult(palette, InterchangeReport(self.info.id))

    def encode(self, palette: CustomPalette) -> ExportResult:
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(_HEADER)
        for index, color in enumerate(palette.colors):
            writer.writerow((index, *color))
        return ExportResult(
            output.getvalue().encode(),
            InterchangeReport(self.info.id, metadata_loss(palette, self.info.preserves)),
        )


CODEC = CsvCodec()
