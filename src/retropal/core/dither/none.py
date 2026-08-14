"""Palette mapping without dithering."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from PIL import Image

from retropal.core.dither.base import DitherAlgorithm
from retropal.core.dither.common import nearest_color
from retropal.palettes.base import RGBColor


def apply_none(image: Image.Image, palette: tuple[RGBColor, ...]) -> Image.Image:
    """Map every opaque pixel to its nearest palette color."""

    output = Image.new("RGBA", image.size)
    output_pixels: list[tuple[int, int, int, int]] = []
    input_pixels = cast(
        Iterable[tuple[int, int, int, int]], image.convert("RGBA").get_flattened_data()
    )
    for red, green, blue, alpha in input_pixels:
        if alpha == 0:
            output_pixels.append((0, 0, 0, 0))
        else:
            mapped = nearest_color((red, green, blue), palette)
            output_pixels.append((*mapped, alpha))
    output.putdata(output_pixels)
    return output


ALGORITHM = DitherAlgorithm("none", "None", apply_none)
