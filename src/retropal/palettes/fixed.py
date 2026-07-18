"""Fixed palette loading and registry."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files

from retropal.palettes.base import PaletteInfo, RGBColor


@dataclass(frozen=True, slots=True)
class FixedPalette:
    id: str
    name: str
    colors: tuple[RGBColor, ...]
    info: PaletteInfo


def load_fixed_palette(palette_id: str) -> FixedPalette:
    resource = files("retropal.palettes.definitions").joinpath(f"{palette_id}.json")
    if not resource.is_file():
        raise KeyError(f"Unknown fixed palette: {palette_id}")
    payload = json.loads(resource.read_text(encoding="utf-8"))
    colors = tuple(tuple(color) for color in payload["colors"])
    info = PaletteInfo(
        id=payload["id"],
        name=payload["name"],
        family=payload["family"],
        manufacturer=payload["manufacturer"],
        year=payload.get("year"),
        color_count=len(colors),
        description=payload["description"],
        tags=tuple(payload.get("tags", ())),
    )
    return FixedPalette(id=info.id, name=info.name, colors=colors, info=info)


def fixed_palette_ids() -> tuple[str, ...]:
    return (
        "gameboy",
        "pico8",
        "ega",
        "dawnbringer16",
        "commodore-64",
        "vic-20",
        "commodore-plus4",
    )
