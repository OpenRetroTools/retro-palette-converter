"""Amiga OCS 12-bit RGB palette generation."""

from __future__ import annotations

from collections import Counter

from PIL import Image

from retropal.palettes.base import RGBColor


def quantize_channel_to_4bit(value: int) -> int:
    if not 0 <= value <= 255:
        raise ValueError("RGB channel values must be between 0 and 255.")
    return round(value / 17) * 17


def quantize_color_to_ocs(color: RGBColor) -> RGBColor:
    return tuple(quantize_channel_to_4bit(channel) for channel in color)


def generate_ocs_palette(image: Image.Image, color_count: int) -> tuple[RGBColor, ...]:
    if color_count not in {16, 32}:
        raise ValueError("Amiga OCS palettes currently support 16 or 32 colors.")

    rgba = image.convert("RGBA")
    opaque_rgb = [(r, g, b) for r, g, b, alpha in rgba.get_flattened_data() if alpha > 0]
    if not opaque_rgb:
        return ((0, 0, 0),)

    snapped = [quantize_color_to_ocs(color) for color in opaque_rgb]
    histogram = Counter(snapped)
    unique = tuple(color for color, _ in histogram.most_common())
    if len(unique) <= color_count:
        return unique

    sample = Image.new("RGB", (len(opaque_rgb), 1))
    sample.putdata(opaque_rgb)
    quantized = sample.quantize(colors=color_count, method=Image.Quantize.MEDIANCUT)
    raw_palette = quantized.getpalette() or []
    candidates: list[RGBColor] = []
    for index in range(color_count):
        offset = index * 3
        candidate = quantize_color_to_ocs(tuple(raw_palette[offset : offset + 3]))
        if candidate not in candidates:
            candidates.append(candidate)

    for color in unique:
        if len(candidates) >= color_count:
            break
        if color not in candidates:
            candidates.append(color)
    return tuple(candidates[:color_count])
