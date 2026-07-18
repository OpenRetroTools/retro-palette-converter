"""Common dithering algorithm interface."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image

from retropal.palettes.base import RGBColor

DitherFunction = Callable[[Image.Image, tuple[RGBColor, ...]], Image.Image]


@dataclass(frozen=True, slots=True)
class DitherAlgorithm:
    """A registered dithering implementation."""

    id: str
    display_name: str
    apply: DitherFunction
