"""Atkinson error-diffusion dithering."""

from __future__ import annotations

from typing import cast

from PIL import Image

from retropal.core.dither.base import DitherAlgorithm
from retropal.core.dither.common import nearest_color
from retropal.palettes.base import RGBColor


def apply_atkinson(
    image: Image.Image,
    palette: tuple[RGBColor, ...],
) -> Image.Image:
    """Map an image using Atkinson error diffusion."""

    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = [
        [cast(tuple[int, int, int, int], rgba.getpixel((x, y))) for x in range(width)]
        for y in range(height)
    ]
    work = [[list(map(float, pixel[:3])) for pixel in row] for row in pixels]
    alpha = [[pixel[3] for pixel in row] for row in pixels]
    output = Image.new("RGBA", rgba.size)

    for y in range(height):
        for x in range(width):
            if alpha[y][x] == 0:
                output.putpixel((x, y), (0, 0, 0, 0))
                continue

            old = work[y][x]
            new = nearest_color(tuple(old), palette)
            output.putpixel((x, y), (*new, alpha[y][x]))
            error = [old[channel] - new[channel] for channel in range(3)]

            for dx, dy in (
                (1, 0),
                (2, 0),
                (-1, 1),
                (0, 1),
                (1, 1),
                (0, 2),
            ):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and alpha[ny][nx] > 0:
                    for channel in range(3):
                        work[ny][nx][channel] = min(
                            255.0,
                            max(0.0, work[ny][nx][channel] + error[channel] / 8),
                        )

    return output


ALGORITHM = DitherAlgorithm("atkinson", "Atkinson", apply_atkinson)
