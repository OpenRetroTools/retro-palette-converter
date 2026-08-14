"""Image loading, inspection, and saving helpers."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import cast

from PIL import Image

from retropal.core.models import ImageInfo


def load_image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source.load()
        return source.convert("RGBA")


def save_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG", optimize=True)


def inspect_image(path: Path) -> ImageInfo:
    image = load_image(path)
    rgb_colors: set[tuple[int, int, int]] = set()
    has_alpha = False
    pixels = cast(Iterable[tuple[int, int, int, int]], image.get_flattened_data())
    for red, green, blue, alpha in pixels:
        if alpha > 0:
            rgb_colors.add((red, green, blue))
        if alpha < 255:
            has_alpha = True
    return ImageInfo(
        width=image.width,
        height=image.height,
        mode="RGBA",
        unique_rgb_colors=len(rgb_colors),
        has_alpha=has_alpha,
    )
