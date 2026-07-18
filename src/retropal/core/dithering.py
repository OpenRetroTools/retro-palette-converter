"""Palette mapping and Floyd-Steinberg dithering."""

from __future__ import annotations

from PIL import Image

from retropal.palettes.base import RGBColor


def nearest_color(rgb: tuple[float, float, float], palette: tuple[RGBColor, ...]) -> RGBColor:
    return min(
        palette,
        key=lambda color: sum((rgb[channel] - color[channel]) ** 2 for channel in range(3)),
    )


def map_without_dither(image: Image.Image, palette: tuple[RGBColor, ...]) -> Image.Image:
    output = Image.new("RGBA", image.size)
    pixels = []
    for r, g, b, alpha in image.convert("RGBA").get_flattened_data():
        if alpha == 0:
            pixels.append((0, 0, 0, 0))
        else:
            nr, ng, nb = nearest_color((r, g, b), palette)
            pixels.append((nr, ng, nb, alpha))
    output.putdata(pixels)
    return output


def map_floyd_steinberg(image: Image.Image, palette: tuple[RGBColor, ...]) -> Image.Image:
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
            neighbors = (
                (1, 0, 7 / 16),
                (-1, 1, 3 / 16),
                (0, 1, 5 / 16),
                (1, 1, 1 / 16),
            )
            for dx, dy, factor in neighbors:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and alpha[ny][nx] > 0:
                    for channel in range(3):
                        work[ny][nx][channel] = min(
                            255.0,
                            max(0.0, work[ny][nx][channel] + error[channel] * factor),
                        )
    return output
