"""Palette metadata and export helpers."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import cast

from PIL import Image

from retropal.palettes import palette_colors
from retropal.palettes.base import RGBColor


def used_colors(image: Image.Image) -> tuple[RGBColor, ...]:
    """Return opaque RGB colors in first-use order."""
    seen: set[RGBColor] = set()
    colors: list[RGBColor] = []
    pixels = cast(Iterable[tuple[int, int, int, int]], image.convert("RGBA").get_flattened_data())
    for red, green, blue, alpha in pixels:
        color = (red, green, blue)
        if alpha > 0 and color not in seen:
            seen.add(color)
            colors.append(color)
    return tuple(colors)


def palette_for_result(
    source: Image.Image,
    converted: Image.Image,
    palette_id: str,
    *,
    declared_palette: tuple[RGBColor, ...] | None = None,
) -> tuple[RGBColor, ...]:
    """Return the declared palette filtered to colors used by the result."""
    declared = (
        declared_palette if declared_palette is not None else palette_colors(palette_id, source)
    )
    active = set(used_colors(converted))
    return tuple(color for color in declared if color in active)


def amiga_ocs_word(color: RGBColor) -> str:
    """Format an OCS color as a three-digit hexadecimal $RGB word."""
    red, green, blue = (round(channel / 17) for channel in color)
    return f"${red:X}{green:X}{blue:X}"


def export_gpl(path: Path, name: str, colors: tuple[RGBColor, ...]) -> Path:
    """Export a GIMP/GrafX2-compatible GPL palette."""
    lines = ["GIMP Palette", f"Name: {name}", "Columns: 8", "#"]
    for index, (red, green, blue) in enumerate(colors):
        lines.append(f"{red:3d} {green:3d} {blue:3d}\tColor {index + 1}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def export_json(path: Path, palette_id: str, colors: tuple[RGBColor, ...]) -> Path:
    """Export palette metadata as readable JSON."""
    payload: dict[str, object] = {
        "palette": palette_id,
        "color_count": len(colors),
        "colors": [
            {
                "rgb": list(color),
                "hex": "#" + "".join(f"{channel:02X}" for channel in color),
            }
            for color in colors
        ],
    }
    if palette_id.startswith("amiga-ocs-"):
        payload["color_space"] = "Amiga OCS 12-bit RGB"
        payload["amiga_ocs_words"] = [amiga_ocs_word(color) for color in colors]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
