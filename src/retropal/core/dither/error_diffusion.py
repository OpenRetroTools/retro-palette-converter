"""Reusable error-diffusion dithering implementations."""

from __future__ import annotations

from collections.abc import Sequence

from PIL import Image

from retropal.core.dither.base import DitherAlgorithm, DitherFunction
from retropal.core.dither.common import nearest_color
from retropal.palettes.base import RGBColor

DiffusionTap = tuple[int, int, float]


def _error_diffusion(
    image: Image.Image,
    palette: tuple[RGBColor, ...],
    taps: Sequence[DiffusionTap],
) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    work = [
        [list(map(float, rgba.getpixel((x, y))[:3])) for x in range(width)] for y in range(height)
    ]
    alpha = [[rgba.getpixel((x, y))[3] for x in range(width)] for y in range(height)]
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

            for dx, dy, factor in taps:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and alpha[ny][nx] > 0:
                    for channel in range(3):
                        work[ny][nx][channel] = min(
                            255.0,
                            max(0.0, work[ny][nx][channel] + error[channel] * factor),
                        )

    return output


def _make_apply(taps: Sequence[DiffusionTap]) -> DitherFunction:
    def apply(image: Image.Image, palette: tuple[RGBColor, ...]) -> Image.Image:
        return _error_diffusion(image, palette, taps)

    return apply


SIERRA_LITE_TAPS: tuple[DiffusionTap, ...] = (
    (1, 0, 2 / 4),
    (-1, 1, 1 / 4),
    (0, 1, 1 / 4),
)

SIERRA_TAPS: tuple[DiffusionTap, ...] = (
    (1, 0, 5 / 32),
    (2, 0, 3 / 32),
    (-2, 1, 2 / 32),
    (-1, 1, 4 / 32),
    (0, 1, 5 / 32),
    (1, 1, 4 / 32),
    (2, 1, 2 / 32),
    (-1, 2, 2 / 32),
    (0, 2, 3 / 32),
    (1, 2, 2 / 32),
)

BURKES_TAPS: tuple[DiffusionTap, ...] = (
    (1, 0, 8 / 32),
    (2, 0, 4 / 32),
    (-2, 1, 2 / 32),
    (-1, 1, 4 / 32),
    (0, 1, 8 / 32),
    (1, 1, 4 / 32),
    (2, 1, 2 / 32),
)

STUCKI_TAPS: tuple[DiffusionTap, ...] = (
    (1, 0, 8 / 42),
    (2, 0, 4 / 42),
    (-2, 1, 2 / 42),
    (-1, 1, 4 / 42),
    (0, 1, 8 / 42),
    (1, 1, 4 / 42),
    (2, 1, 2 / 42),
    (-2, 2, 1 / 42),
    (-1, 2, 2 / 42),
    (0, 2, 4 / 42),
    (1, 2, 2 / 42),
    (2, 2, 1 / 42),
)

JARVIS_JUDICE_NINKE_TAPS: tuple[DiffusionTap, ...] = (
    (1, 0, 7 / 48),
    (2, 0, 5 / 48),
    (-2, 1, 3 / 48),
    (-1, 1, 5 / 48),
    (0, 1, 7 / 48),
    (1, 1, 5 / 48),
    (2, 1, 3 / 48),
    (-2, 2, 1 / 48),
    (-1, 2, 3 / 48),
    (0, 2, 5 / 48),
    (1, 2, 3 / 48),
    (2, 2, 1 / 48),
)

SIERRA_LITE_ALGORITHM = DitherAlgorithm(
    "sierra-lite",
    "Sierra Lite",
    _make_apply(SIERRA_LITE_TAPS),
)
SIERRA_ALGORITHM = DitherAlgorithm("sierra", "Sierra", _make_apply(SIERRA_TAPS))
BURKES_ALGORITHM = DitherAlgorithm("burkes", "Burkes", _make_apply(BURKES_TAPS))
STUCKI_ALGORITHM = DitherAlgorithm("stucki", "Stucki", _make_apply(STUCKI_TAPS))
JARVIS_JUDICE_NINKE_ALGORITHM = DitherAlgorithm(
    "jarvis-judice-ninke",
    "Jarvis–Judice–Ninke",
    _make_apply(JARVIS_JUDICE_NINKE_TAPS),
)
