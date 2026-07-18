"""Palette registry."""

from __future__ import annotations

from PIL import Image

from retropal.palettes.amiga_ocs import generate_ocs_palette
from retropal.palettes.base import RGBColor
from retropal.palettes.fixed import fixed_palette_ids, load_fixed_palette

PALETTE_IDS = (*fixed_palette_ids(), "amiga-ocs-16", "amiga-ocs-32")


def palette_colors(palette_id: str, image: Image.Image) -> tuple[RGBColor, ...]:
    if palette_id == "amiga-ocs-16":
        return generate_ocs_palette(image, 16)
    if palette_id == "amiga-ocs-32":
        return generate_ocs_palette(image, 32)
    return load_fixed_palette(palette_id).colors
