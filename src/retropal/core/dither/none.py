"""Palette mapping without dithering."""

from __future__ import annotations

from PIL import Image

from retropal.core.dither.base import DitherAlgorithm
from retropal.core.dither.common import nearest_color
from retropal.palettes.base import RGBColor


def apply_none(image: Image.Image, palette: tuple[RGBColor, ...]) -> Image.Image:
    """Map every opaque pixel to its nearest palette color."""

    output = Image.new("RGBA", image.size)
    pixels = []
    for red, green, blue, alpha in image.convert("RGBA").get_flattened_data():
        if alpha == 0:
            pixels.append((0, 0, 0, 0))
        else:
            mapped = nearest_color((red, green, blue), palette)
            pixels.append((*mapped, alpha))
    output.putdata(pixels)
    return output


ALGORITHM = DitherAlgorithm("none", "None", apply_none)
