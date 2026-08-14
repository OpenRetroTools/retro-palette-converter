"""Adaptive Amiga palette generation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from PIL import Image

from retropal.palettes.amiga_ocs import generate_ocs_palette
from retropal.palettes.base import RGBColor


def generate_aga_palette(image: Image.Image, color_count: int = 256) -> tuple[RGBColor, ...]:
    rgba = image.convert("RGBA")
    pixels = cast(Iterable[tuple[int, int, int, int]], rgba.get_flattened_data())
    opaque = [(red, green, blue) for red, green, blue, alpha in pixels if alpha > 0]
    if not opaque:
        return ((0, 0, 0),)
    sample = Image.new("RGB", (len(opaque), 1))
    sample.putdata(opaque)
    quantized = sample.quantize(colors=color_count, method=Image.Quantize.MEDIANCUT)
    raw = quantized.getpalette() or []
    used = len(quantized.getcolors() or ())
    return tuple((raw[index * 3], raw[index * 3 + 1], raw[index * 3 + 2]) for index in range(used))


def generate_amiga_palette(image: Image.Image, palette_id: str) -> tuple[RGBColor, ...]:
    if palette_id == "amiga-ocs-16":
        return generate_ocs_palette(image, 16)
    if palette_id == "amiga-ocs-32":
        return generate_ocs_palette(image, 32)
    if palette_id == "amiga-ecs-64":
        return generate_ocs_palette(image, 64)
    if palette_id == "amiga-aga-256":
        return generate_aga_palette(image, 256)
    raise KeyError(f"Unknown adaptive Amiga palette: {palette_id}")
