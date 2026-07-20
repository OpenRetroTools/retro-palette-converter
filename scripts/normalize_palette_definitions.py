#!/usr/bin/env python3
"""Normalize built-in palette JSON files to the canonical metadata schema."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).parents[1]
DEFINITIONS = ROOT / "src/retropal/palettes/definitions"


def color_count(payload: dict[str, Any]) -> int:
    if "colors" in payload:
        return len(payload["colors"])
    if "rgb_levels" in payload:
        return len(payload["rgb_levels"]) ** 3
    return (
        len(payload.get("base_colors", ()))
        + len(payload["color_cube_levels"]) ** 3
        + len(payload.get("grayscale_levels", ()))
    )


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    count = color_count(payload)
    display_name = payload.pop("name", payload.get("display_name"))
    payload["display_name"] = display_name
    payload.setdefault("platform", display_name)
    payload.setdefault("colour_count", count)
    payload.setdefault("bit_depth", f"{max(1, math.ceil(math.log2(count)))}-bit indexed")
    payload.setdefault("dac_size", None)
    payload.setdefault("palette_source", "Bundled canonical palette definition")
    payload.setdefault("notes", payload.get("description", "Canonical conversion palette."))
    preferred = (
        "id",
        "display_name",
        "manufacturer",
        "platform",
        "family",
        "year",
        "colour_count",
        "bit_depth",
        "dac_size",
        "palette_source",
        "description",
        "notes",
        "tags",
        "platform_family",
        "generation",
    )
    return {key: payload[key] for key in preferred if key in payload} | {
        key: value for key, value in payload.items() if key not in preferred
    }


def main() -> int:
    for path in sorted(DEFINITIONS.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(
            json.dumps(normalize(payload), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
