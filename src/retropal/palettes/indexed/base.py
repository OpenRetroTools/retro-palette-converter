"""Typed results and errors for indexed-image palette extraction."""

from __future__ import annotations

from dataclasses import dataclass

from retropal.palettes.custom import CustomPalette, CustomPaletteError


class IndexedPaletteError(CustomPaletteError):
    """An unsupported or malformed indexed image palette."""


@dataclass(frozen=True, slots=True)
class IndexedTransparency:
    """Per-palette-index alpha values kept outside the RGB palette model."""

    alpha_by_index: tuple[int, ...]

    def __post_init__(self) -> None:
        if not self.alpha_by_index or any(
            type(alpha) is not int or not 0 <= alpha <= 255 for alpha in self.alpha_by_index
        ):
            raise IndexedPaletteError("Indexed transparency must contain alpha values 0..255")

    @property
    def non_opaque_indexes(self) -> tuple[int, ...]:
        return tuple(index for index, alpha in enumerate(self.alpha_by_index) if alpha < 255)


@dataclass(frozen=True, slots=True)
class IndexedPaletteResult:
    palette: CustomPalette
    source_format: str
    stored_entry_count: int
    width: int
    height: int
    used_indexes: tuple[int, ...]
    unused_indexes: tuple[int, ...]
    highest_used_index: int | None
    transparency: IndexedTransparency | None = None
    frame_index: int | None = None
    frame_count: int = 1
    messages: tuple[str, ...] = ()
    all_stored_semantics_preserved: bool = True


def usage_statistics(
    indexes: set[int], entry_count: int
) -> tuple[tuple[int, ...], tuple[int, ...], int | None]:
    """Validate referenced indexes and return stable usage statistics."""
    if indexes and max(indexes) >= entry_count:
        raise IndexedPaletteError(
            f"Pixel index {max(indexes)} references missing palette entry; "
            f"stored palette has {entry_count} entries"
        )
    used = tuple(sorted(indexes))
    unused = tuple(index for index in range(entry_count) if index not in indexes)
    return used, unused, used[-1] if used else None
