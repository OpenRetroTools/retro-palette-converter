"""Palette conversion service."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from retropal.core.dithering import map_floyd_steinberg, map_without_dither
from retropal.core.image_io import load_image, save_png
from retropal.core.models import DitherMode
from retropal.palettes import palette_colors


def convert(
    image: Image.Image,
    palette_id: str,
    dither: DitherMode = DitherMode.NONE,
) -> Image.Image:
    colors = palette_colors(palette_id, image)
    if dither == DitherMode.NONE:
        return map_without_dither(image, colors)
    if dither == DitherMode.FLOYD_STEINBERG:
        return map_floyd_steinberg(image, colors)
    raise ValueError(f"Unsupported dithering mode: {dither}")


def convert_file(
    input_path: Path,
    output_path: Path,
    palette_id: str,
    dither: DitherMode,
) -> None:
    save_png(convert(load_image(input_path), palette_id, dither), output_path)
