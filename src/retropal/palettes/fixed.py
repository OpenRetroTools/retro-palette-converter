"""Fixed palette loading and registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files

from retropal.palettes.base import RGBColor


@dataclass(frozen=True, slots=True)
class FixedPalette:
    id: str
    name: str
    colors: tuple[RGBColor, ...]


def load_fixed_palette(palette_id: str) -> FixedPalette:
    resource = files("retropal.palettes.definitions").joinpath(f"{palette_id}.json")
    if not resource.is_file():
        raise KeyError(f"Unknown fixed palette: {palette_id}")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    colors = tuple(tuple(color) for color in payload["colors"])
    return FixedPalette(id=payload["id"], name=payload["name"], colors=colors)


def fixed_palette_ids() -> tuple[str, ...]:
    return ("gameboy", "pico8", "ega", "dawnbringer16")
