"""Narrow Pillow use for decoded PNG/GIF palette-index statistics."""

from __future__ import annotations

from collections.abc import Iterable
from io import BytesIO
from typing import cast

from PIL import Image, UnidentifiedImageError

from retropal.palettes.indexed.base import IndexedPaletteError


def pillow_index_usage(data: bytes, expected_format: str) -> tuple[int, int, set[int]]:
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != expected_format or image.mode != "P":
                raise IndexedPaletteError(
                    f"{expected_format} image is not palette-indexed (mode {image.mode})"
                )
            image.seek(0)
            image.load()
            pixels = cast(Iterable[int], image.get_flattened_data())
            return image.width, image.height, set(pixels)
    except IndexedPaletteError:
        raise
    except (OSError, UnidentifiedImageError, ValueError) as exc:
        raise IndexedPaletteError(f"Could not decode indexed {expected_format}: {exc}") from exc
