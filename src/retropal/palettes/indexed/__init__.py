"""Indexed-image stored-palette extraction."""

from retropal.palettes.indexed.base import (
    IndexedPaletteError,
    IndexedPaletteResult,
    IndexedTransparency,
)
from retropal.palettes.indexed.service import INDEXED_IMAGE_FORMATS, extract_indexed_palette

__all__ = [
    "INDEXED_IMAGE_FORMATS",
    "IndexedPaletteError",
    "IndexedPaletteResult",
    "IndexedTransparency",
    "extract_indexed_palette",
]
