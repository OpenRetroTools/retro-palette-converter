"""Palette conversion service."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from retropal.core.dither import get_dither
from retropal.core.image_io import load_image, save_png
from retropal.core.models import DitherMode
from retropal.palettes import palette_colors


def convert(
    image: Image.Image,
    palette_id: str,
    dither: str | DitherMode = DitherMode.NONE,
) -> Image.Image:
    colors = palette_colors(palette_id, image)
    dither_id = dither.value if isinstance(dither, DitherMode) else str(dither)
    return get_dither(dither_id).apply(image, colors)


def convert_file(
    input_path: Path,
    output_path: Path,
    palette_id: str,
    dither: str | DitherMode,
) -> None:
    save_png(convert(load_image(input_path), palette_id, dither), output_path)
