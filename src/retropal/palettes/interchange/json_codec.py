"""Portable JSON interchange codec, separate from native persistence."""

from __future__ import annotations

import json
from typing import Any

from retropal.palettes.custom import CustomPalette, CustomPaletteError
from retropal.palettes.interchange.base import (
    CodecInfo,
    ExportResult,
    ImportResult,
    InterchangeReport,
    PaletteCodecError,
    decode_text,
)

SCHEMA = "org.openretrotools.palette-interchange"
VERSION = 1


class JsonCodec:
    info = CodecInfo(
        "json",
        "JSON palette interchange",
        (".json",),
        False,
        ("id", "name", "colors", "description", "source"),
    )

    def sniff(self, data: bytes) -> bool:
        try:
            payload: Any = json.loads(data.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return False
        return isinstance(payload, dict) and payload.get("schema") == SCHEMA

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult:
        del palette_id, fallback_name
        try:
            payload: Any = json.loads(decode_text(data, self.info.name))
        except json.JSONDecodeError as exc:
            raise PaletteCodecError(
                f"Malformed interchange JSON at line {exc.lineno}, column {exc.colno}"
            ) from exc
        if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
            raise PaletteCodecError("Invalid JSON palette interchange schema")
        if payload.get("version") != VERSION:
            raise PaletteCodecError(
                f"Unsupported JSON palette interchange version: {payload.get('version')!r}"
            )
        required = {"schema", "version", "id", "name", "colors", "description", "source"}
        if payload.keys() != required:
            raise PaletteCodecError("Invalid JSON palette interchange fields")
        try:
            palette = CustomPalette(
                payload["id"],
                payload["name"],
                tuple(payload["colors"]),
                payload["description"],
                payload["source"],
            )
        except (KeyError, TypeError, CustomPaletteError) as exc:
            raise PaletteCodecError(f"Invalid JSON interchange palette: {exc}") from exc
        return ImportResult(palette, InterchangeReport(self.info.id))

    def encode(self, palette: CustomPalette) -> ExportResult:
        payload = {
            "schema": SCHEMA,
            "version": VERSION,
            "id": palette.id,
            "name": palette.name,
            "colors": [list(color) for color in palette.colors],
            "description": palette.description,
            "source": palette.source,
        }
        return ExportResult(
            (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode(),
            InterchangeReport(self.info.id),
        )


CODEC = JsonCodec()
