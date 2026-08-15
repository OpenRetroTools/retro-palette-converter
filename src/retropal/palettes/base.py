"""Palette types and metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

RGBColor = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class PaletteInfo:
    id: str
    name: str
    family: str
    manufacturer: str
    year: int | None
    color_count: int
    description: str
    tags: tuple[str, ...] = ()
    adaptive: bool = False
    platform: str | None = None
    notes: str = ""
    generation: str | None = None
    platform_family: str | None = None
    bit_depth: str | None = None
    dac_size: str | None = None
    palette_source: str | None = None
    alias_of: str | None = None


class Palette(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def colors(self) -> tuple[RGBColor, ...]: ...

    @property
    def info(self) -> PaletteInfo: ...
