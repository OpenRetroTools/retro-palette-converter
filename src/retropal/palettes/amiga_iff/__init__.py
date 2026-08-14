"""Amiga IFF/ILBM palette interchange and metadata preservation."""

from retropal.palettes.amiga_iff.base import (
    ColorCycleRange,
    IffChunk,
    IlbmDocument,
    IlbmImportResult,
    IlbmPaletteError,
    IlbmWriteResult,
)
from retropal.palettes.amiga_iff.parser import parse_ilbm, serialize_ilbm
from retropal.palettes.amiga_iff.service import (
    import_ilbm_palette,
    inspect_ilbm,
    replace_ilbm_palette,
)

__all__ = [
    "ColorCycleRange",
    "IffChunk",
    "IlbmDocument",
    "IlbmImportResult",
    "IlbmPaletteError",
    "IlbmWriteResult",
    "import_ilbm_palette",
    "inspect_ilbm",
    "parse_ilbm",
    "replace_ilbm_palette",
    "serialize_ilbm",
]
