"""Palette registry, metadata, and colour resolution."""

from __future__ import annotations

from PIL import Image

from retropal.palettes.amiga import generate_amiga_palette
from retropal.palettes.base import PaletteInfo, RGBColor
from retropal.palettes.fixed import fixed_palette_ids, load_fixed_palette

_ADAPTIVE_INFO = (
    PaletteInfo(
        "amiga-ocs-16",
        "Amiga OCS 16",
        "Amiga",
        "Commodore",
        1985,
        16,
        "Adaptive 16-colour palette snapped to the Amiga OCS 12-bit RGB colour space.",
        ("amiga", "ocs"),
        True,
    ),
    PaletteInfo(
        "amiga-ocs-32",
        "Amiga OCS 32",
        "Amiga",
        "Commodore",
        1985,
        32,
        "Adaptive 32-colour palette snapped to the Amiga OCS 12-bit RGB colour space.",
        ("amiga", "ocs"),
        True,
    ),
    PaletteInfo(
        "amiga-ecs-64",
        "Amiga ECS 64",
        "Amiga",
        "Commodore",
        1990,
        64,
        "Adaptive 64-colour palette for ECS-era workflows, using the 12-bit base colour space.",
        ("amiga", "ecs", "ehb"),
        True,
    ),
    PaletteInfo(
        "amiga-aga-256",
        "Amiga AGA 256",
        "Amiga",
        "Commodore",
        1992,
        256,
        "Adaptive 256-colour palette using AGA's 24-bit palette registers.",
        ("amiga", "aga"),
        True,
    ),
)
_ADAPTIVE_BY_ID = {info.id: info for info in _ADAPTIVE_INFO}
PALETTE_IDS = (*fixed_palette_ids(), *tuple(info.id for info in _ADAPTIVE_INFO))


def palette_colors(palette_id: str, image: Image.Image) -> tuple[RGBColor, ...]:
    if palette_id in _ADAPTIVE_BY_ID:
        return generate_amiga_palette(image, palette_id)
    return load_fixed_palette(palette_id).colors


def get_palette_info(palette_id: str) -> PaletteInfo:
    if palette_id in _ADAPTIVE_BY_ID:
        return _ADAPTIVE_BY_ID[palette_id]
    return load_fixed_palette(palette_id).info


def iter_palette_info() -> tuple[PaletteInfo, ...]:
    return tuple(get_palette_info(palette_id) for palette_id in PALETTE_IDS)


def list_families() -> tuple[str, ...]:
    return tuple(dict.fromkeys(info.family for info in iter_palette_info()))


def list_by_family(family: str) -> tuple[PaletteInfo, ...]:
    return tuple(
        info for info in iter_palette_info() if info.family.casefold() == family.casefold()
    )


def list_by_manufacturer(manufacturer: str) -> tuple[PaletteInfo, ...]:
    return tuple(
        info
        for info in iter_palette_info()
        if info.manufacturer.casefold() == manufacturer.casefold()
    )
