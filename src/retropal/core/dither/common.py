"""Shared palette-mapping helpers."""

from __future__ import annotations

from functools import lru_cache

from retropal.palettes.base import RGBColor


@lru_cache(maxsize=65_536)
def nearest_color(rgb: tuple[float, float, float], palette: tuple[RGBColor, ...]) -> RGBColor:
    """Return the palette color nearest to an RGB value."""

    return min(
        palette,
        key=lambda color: sum((rgb[channel] - color[channel]) ** 2 for channel in range(3)),
    )
