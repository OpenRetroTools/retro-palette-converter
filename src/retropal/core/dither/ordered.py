"""Ordered Bayer dithering implementations."""

from __future__ import annotations

from collections.abc import Sequence
from typing import cast

from PIL import Image

from retropal.core.dither.base import DitherAlgorithm, DitherFunction
from retropal.core.dither.common import nearest_color
from retropal.palettes.base import RGBColor

BAYER_2: tuple[tuple[int, ...], ...] = (
    (0, 2),
    (3, 1),
)
BAYER_4: tuple[tuple[int, ...], ...] = (
    (0, 8, 2, 10),
    (12, 4, 14, 6),
    (3, 11, 1, 9),
    (15, 7, 13, 5),
)
BAYER_8: tuple[tuple[int, ...], ...] = (
    (0, 32, 8, 40, 2, 34, 10, 42),
    (48, 16, 56, 24, 50, 18, 58, 26),
    (12, 44, 4, 36, 14, 46, 6, 38),
    (60, 28, 52, 20, 62, 30, 54, 22),
    (3, 35, 11, 43, 1, 33, 9, 41),
    (51, 19, 59, 27, 49, 17, 57, 25),
    (15, 47, 7, 39, 13, 45, 5, 37),
    (63, 31, 55, 23, 61, 29, 53, 21),
)


def _ordered_dither(
    image: Image.Image,
    palette: tuple[RGBColor, ...],
    matrix: Sequence[Sequence[int]],
) -> Image.Image:
    rgba = image.convert("RGBA")
    output = Image.new("RGBA", rgba.size)
    size = len(matrix)
    levels = size * size
    # TODO: Evaluate amplitude against target-palette quantization characteristics
    # using visual comparisons and regression evidence before changing this value.
    amplitude = 64.0

    for y in range(rgba.height):
        for x in range(rgba.width):
            red, green, blue, alpha = cast(tuple[int, int, int, int], rgba.getpixel((x, y)))
            if alpha == 0:
                output.putpixel((x, y), (0, 0, 0, 0))
                continue

            threshold = (matrix[y % size][x % size] + 0.5) / levels - 0.5
            offset = threshold * amplitude
            adjusted = tuple(
                min(255.0, max(0.0, channel + offset)) for channel in (red, green, blue)
            )
            output.putpixel((x, y), (*nearest_color(adjusted, palette), alpha))

    return output


def _make_apply(matrix: Sequence[Sequence[int]]) -> DitherFunction:
    def apply(image: Image.Image, palette: tuple[RGBColor, ...]) -> Image.Image:
        return _ordered_dither(image, palette, matrix)

    return apply


BAYER_2_ALGORITHM = DitherAlgorithm("bayer-2x2", "Bayer 2×2", _make_apply(BAYER_2))
BAYER_4_ALGORITHM = DitherAlgorithm("bayer-4x4", "Bayer 4×4", _make_apply(BAYER_4))
BAYER_8_ALGORITHM = DitherAlgorithm("bayer-8x8", "Bayer 8×8", _make_apply(BAYER_8))
