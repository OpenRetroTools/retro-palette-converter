"""Shared domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DitherMode(StrEnum):
    NONE = "none"
    FLOYD_STEINBERG = "floyd-steinberg"


@dataclass(frozen=True, slots=True)
class ImageInfo:
    width: int
    height: int
    mode: str
    unique_rgb_colors: int
    has_alpha: bool
