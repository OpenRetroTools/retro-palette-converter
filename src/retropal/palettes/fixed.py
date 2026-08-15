"""Validated, automatically discovered fixed-palette definitions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from importlib.resources.abc import Traversable
from typing import Any

from retropal.palettes.base import PaletteInfo, RGBColor

REQUIRED_METADATA_FIELDS = frozenset(
    {
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
        "tags",
        "notes",
    }
)


@dataclass(frozen=True, slots=True)
class FixedPalette:
    id: str
    display_name: str
    colors: tuple[RGBColor, ...]
    info: PaletteInfo

    @property
    def name(self) -> str:
        """Backward-compatible alias for the user-facing display name."""
        return self.display_name


def _definition_resources() -> tuple[Traversable, ...]:
    definitions = files("retropal.palettes.definitions")
    return tuple(
        sorted(
            (item for item in definitions.iterdir() if item.name.endswith(".json")),
            key=lambda item: item.name,
        )
    )


def _colors_from_payload(payload: dict[str, Any]) -> tuple[RGBColor, ...]:
    if "colors" in payload:
        return tuple(tuple(color) for color in payload["colors"])
    if "rgb_levels" in payload:
        levels = tuple(payload["rgb_levels"])
        return tuple((red, green, blue) for red in levels for green in levels for blue in levels)
    base_colors = tuple(tuple(color) for color in payload.get("base_colors", ()))
    levels = tuple(payload["color_cube_levels"])
    cube = tuple((red, green, blue) for red in levels for green in levels for blue in levels)
    grayscale = tuple((level, level, level) for level in payload.get("grayscale_levels", ()))
    return base_colors + cube + grayscale


def _validate_payload(payload: dict[str, Any], source: str) -> None:
    missing = REQUIRED_METADATA_FIELDS - payload.keys()
    if missing:
        raise ValueError(f"Palette definition {source} is missing: {', '.join(sorted(missing))}")
    if not isinstance(payload["tags"], list) or not all(
        isinstance(tag, str) for tag in payload["tags"]
    ):
        raise ValueError(f"Palette definition {source} has invalid tags")
    if not isinstance(payload["year"], int) or payload["year"] <= 0:
        raise ValueError(f"Palette definition {source} has an invalid year")
    for field in (
        "id",
        "display_name",
        "manufacturer",
        "platform",
        "family",
        "bit_depth",
        "palette_source",
        "notes",
    ):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ValueError(f"Palette definition {source} has invalid {field}")
    alias_of = payload.get("alias_of")
    if alias_of is not None and (not isinstance(alias_of, str) or not alias_of.strip()):
        raise ValueError(f"Palette definition {source} has invalid alias_of")


def _palette_from_payload(payload: dict[str, Any], source: str) -> FixedPalette:
    _validate_payload(payload, source)
    colors = _colors_from_payload(payload)
    if payload["colour_count"] != len(colors):
        raise ValueError(
            f"Palette definition {source} declares {payload['colour_count']} colours "
            f"but contains {len(colors)}"
        )
    if any(
        len(color) != 3 or any(not 0 <= channel <= 255 for channel in color) for color in colors
    ):
        raise ValueError(f"Palette definition {source} contains an invalid RGB colour")
    info = PaletteInfo(
        id=payload["id"],
        name=payload["display_name"],
        family=payload["family"],
        manufacturer=payload["manufacturer"],
        year=payload["year"],
        color_count=len(colors),
        description=payload.get("description", payload["notes"]),
        tags=tuple(payload["tags"]),
        platform=payload["platform"],
        notes=payload["notes"],
        generation=payload.get("generation"),
        platform_family=payload.get("platform_family"),
        bit_depth=payload["bit_depth"],
        dac_size=payload["dac_size"],
        palette_source=payload["palette_source"],
        alias_of=payload.get("alias_of"),
    )
    return FixedPalette(info.id, info.name, colors, info)


@cache
def _fixed_palettes() -> dict[str, FixedPalette]:
    palettes: dict[str, FixedPalette] = {}
    names: dict[str, str] = {}
    for resource in _definition_resources():
        payload = json.loads(resource.read_text(encoding="utf-8"))
        palette = _palette_from_payload(payload, resource.name)
        if palette.id in palettes:
            raise ValueError(f"Duplicate palette ID: {palette.id}")
        folded_name = palette.display_name.casefold()
        if folded_name in names:
            raise ValueError(
                f"Duplicate palette display name: {palette.display_name} "
                f"({names[folded_name]}, {palette.id})"
            )
        palettes[palette.id] = palette
        names[folded_name] = palette.id
    for palette in palettes.values():
        target_id = palette.info.alias_of
        if target_id is None:
            continue
        if target_id == palette.id:
            raise ValueError(f"Palette {palette.id} cannot alias itself")
        target = palettes.get(target_id)
        if target is None:
            raise ValueError(f"Palette {palette.id} aliases unknown palette: {target_id}")
        if target.info.alias_of is not None:
            raise ValueError(f"Palette {palette.id} aliases another alias: {target_id}")
        if palette.colors != target.colors:
            raise ValueError(f"Palette {palette.id} does not match alias target: {target_id}")
    return palettes


def load_fixed_palette(palette_id: str) -> FixedPalette:
    try:
        return _fixed_palettes()[palette_id]
    except KeyError as exc:
        raise KeyError(f"Unknown fixed palette: {palette_id}") from exc


def fixed_palette_ids() -> tuple[str, ...]:
    """Return fixed palette IDs discovered from packaged JSON resources."""
    return tuple(_fixed_palettes())
