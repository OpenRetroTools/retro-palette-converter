"""Format-independent custom palette domain model."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

from retropal.palettes.base import RGBColor

_PALETTE_ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class CustomPaletteError(ValueError):
    """A controlled custom-palette validation or lifecycle error."""


def validate_palette_id(palette_id: str) -> str:
    """Validate and return a stable custom palette identifier."""
    if not isinstance(palette_id, str) or not _PALETTE_ID.fullmatch(palette_id):
        raise CustomPaletteError(
            "Palette ID must start with a lowercase letter and contain only "
            "lowercase letters, numbers, and single hyphens"
        )
    return palette_id


def validate_color(color: object, *, index: int | None = None) -> RGBColor:
    """Validate one exact three-channel RGB entry."""
    location = f" at index {index}" if index is not None else ""
    if not isinstance(color, (list, tuple)) or len(color) != 3:
        raise CustomPaletteError(f"Invalid RGB colour{location}: expected three channels")
    if any(type(channel) is not int or not 0 <= channel <= 255 for channel in color):
        raise CustomPaletteError(f"Invalid RGB colour{location}: channels must be integers 0..255")
    return color[0], color[1], color[2]


@dataclass(frozen=True, slots=True)
class CustomPalette:
    """An immutable, ordered user palette independent of any file format."""

    id: str
    name: str
    colors: tuple[RGBColor, ...]
    description: str = ""
    source: str | None = None

    def __post_init__(self) -> None:
        validate_palette_id(self.id)
        if not isinstance(self.name, str) or not self.name.strip():
            raise CustomPaletteError("Palette name must not be empty")
        if not isinstance(self.description, str):
            raise CustomPaletteError("Palette description must be a string")
        if self.source is not None and not isinstance(self.source, str):
            raise CustomPaletteError("Palette source must be a string or None")
        if not self.colors:
            raise CustomPaletteError("Palette must contain at least one colour")
        validated = tuple(
            validate_color(color, index=index) for index, color in enumerate(self.colors)
        )
        object.__setattr__(self, "colors", validated)

    def rename(self, name: str) -> CustomPalette:
        return replace(self, name=name)

    def replace_colors(self, colors: tuple[RGBColor, ...]) -> CustomPalette:
        return replace(self, colors=colors)

    def add_color(self, color: RGBColor, index: int | None = None) -> CustomPalette:
        validated = validate_color(color)
        insertion = len(self.colors) if index is None else index
        if not 0 <= insertion <= len(self.colors):
            raise CustomPaletteError(f"Colour insertion index out of range: {insertion}")
        return replace(
            self, colors=self.colors[:insertion] + (validated,) + self.colors[insertion:]
        )

    def set_color(self, index: int, color: RGBColor) -> CustomPalette:
        if not 0 <= index < len(self.colors):
            raise CustomPaletteError(f"Colour index out of range: {index}")
        validated = validate_color(color)
        return replace(self, colors=self.colors[:index] + (validated,) + self.colors[index + 1 :])

    def remove_color(self, index: int) -> CustomPalette:
        if not 0 <= index < len(self.colors):
            raise CustomPaletteError(f"Colour index out of range: {index}")
        if len(self.colors) == 1:
            raise CustomPaletteError("Palette must contain at least one colour")
        return replace(self, colors=self.colors[:index] + self.colors[index + 1 :])

    def move_color(self, source_index: int, target_index: int) -> CustomPalette:
        if not 0 <= source_index < len(self.colors):
            raise CustomPaletteError(f"Source colour index out of range: {source_index}")
        if not 0 <= target_index < len(self.colors):
            raise CustomPaletteError(f"Target colour index out of range: {target_index}")
        colors = list(self.colors)
        color = colors.pop(source_index)
        colors.insert(target_index, color)
        return replace(self, colors=tuple(colors))
