"""Palette protocol definitions."""

from __future__ import annotations

from typing import Protocol

RGBColor = tuple[int, int, int]


class Palette(Protocol):
    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def colors(self) -> tuple[RGBColor, ...]: ...
