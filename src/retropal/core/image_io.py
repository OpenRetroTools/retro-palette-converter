"""Image loading, inspection, and saving helpers."""

from __future__ import annotations

from pathlib import Path

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
    rgb_colors = {(r, g, b) for r, g, b, alpha in image.get_flattened_data() if alpha > 0}
    has_alpha = any(alpha < 255 for *_, alpha in image.get_flattened_data())
    return ImageInfo(
        width=image.width,
        height=image.height,
        mode="RGBA",
        unique_rgb_colors=len(rgb_colors),
        has_alpha=has_alpha,
    )
