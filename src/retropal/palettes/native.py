"""Native persistence for custom palettes (not an interchange format)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from retropal.palettes.custom import CustomPalette, CustomPaletteError

NATIVE_SCHEMA = "org.openretrotools.retropal.custom-palette"
NATIVE_SCHEMA_VERSION = 1
NATIVE_SUFFIX = ".retropal-palette.json"


class NativePaletteError(CustomPaletteError):
    """A malformed or unsupported native custom-palette document."""


def save_native_palette(palette: CustomPalette, path: Path) -> Path:
    """Write a deterministic native custom-palette document."""
    payload = {
        "schema": NATIVE_SCHEMA,
        "version": NATIVE_SCHEMA_VERSION,
        "palette": {
            "id": palette.id,
            "name": palette.name,
            "colors": [list(color) for color in palette.colors],
            "description": palette.description,
            "source": palette.source,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def load_native_palette(path: Path) -> CustomPalette:
    """Load and validate a native custom-palette document."""
    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise NativePaletteError(
            f"Malformed native palette JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(payload, dict):
        raise NativePaletteError("Native palette document must be a JSON object")
    if payload.get("schema") != NATIVE_SCHEMA:
        raise NativePaletteError(f"Unsupported native palette schema: {payload.get('schema')!r}")
    if payload.get("version") != NATIVE_SCHEMA_VERSION:
        raise NativePaletteError(f"Unsupported native palette version: {payload.get('version')!r}")
    palette = payload.get("palette")
    if not isinstance(palette, dict):
        raise NativePaletteError("Native palette document is missing the palette object")
    required = {"id", "name", "colors", "description", "source"}
    if palette.keys() != required:
        missing = sorted(required - palette.keys())
        extra = sorted(palette.keys() - required)
        details = []
        if missing:
            details.append(f"missing fields: {', '.join(missing)}")
        if extra:
            details.append(f"unknown fields: {', '.join(extra)}")
        raise NativePaletteError("Invalid native palette fields (" + "; ".join(details) + ")")
    if not isinstance(palette["id"], str) or not isinstance(palette["name"], str):
        raise NativePaletteError("Native palette ID and name must be strings")
    if not isinstance(palette["description"], str):
        raise NativePaletteError("Native palette description must be a string")
    if palette["source"] is not None and not isinstance(palette["source"], str):
        raise NativePaletteError("Native palette source must be a string or null")
    if not isinstance(palette["colors"], list):
        raise NativePaletteError("Native palette colors must be an array")
    try:
        return CustomPalette(
            id=palette["id"],
            name=palette["name"],
            colors=tuple(palette["colors"]),
            description=palette["description"],
            source=palette["source"],
        )
    except CustomPaletteError as exc:
        raise NativePaletteError(f"Invalid native palette: {exc}") from exc
