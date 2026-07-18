"""Shared domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DitherMode(StrEnum):
    NONE = "none"
    FLOYD_STEINBERG = "floyd-steinberg"
    ATKINSON = "atkinson"
    BAYER_2X2 = "bayer-2x2"
    BAYER_4X4 = "bayer-4x4"
    BAYER_8X8 = "bayer-8x8"


@dataclass(frozen=True, slots=True)
class ImageInfo:
    width: int
    height: int
    mode: str
    unique_rgb_colors: int
    has_alpha: bool
