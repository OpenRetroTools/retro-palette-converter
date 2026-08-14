"""Amiga IFF/ILBM palette interchange and metadata preservation."""

from retropal.palettes.amiga_iff.base import (
    ColorCycleRange,
    IffChunk,
    IlbmDocument,
    IlbmImportResult,
    IlbmPaletteError,
    IlbmWriteResult,
)
from retropal.palettes.amiga_iff.cycling import (
    CycleIssueCode,
    CycleIssueSeverity,
    CycleValidationIssue,
    cycle_step,
    palette_at,
    validate_cycles,
)
from retropal.palettes.amiga_iff.parser import parse_ilbm, serialize_ilbm
from retropal.palettes.amiga_iff.preview import (
    IndexedIlbmImage,
    decode_byterun1_rows,
    decode_indexed_ilbm,
    render_indexed_preview,
)
from retropal.palettes.amiga_iff.service import (
    add_ilbm_cycle,
    edit_ilbm_cycle,
    import_ilbm_palette,
    inspect_ilbm,
    remove_ilbm_cycle,
    replace_ilbm_palette,
)

__all__ = [
    "ColorCycleRange",
    "CycleIssueCode",
    "CycleIssueSeverity",
    "CycleValidationIssue",
    "IffChunk",
    "IlbmDocument",
    "IlbmImportResult",
    "IlbmPaletteError",
    "IlbmWriteResult",
    "IndexedIlbmImage",
    "add_ilbm_cycle",
    "cycle_step",
    "decode_byterun1_rows",
    "decode_indexed_ilbm",
    "edit_ilbm_cycle",
    "import_ilbm_palette",
    "inspect_ilbm",
    "parse_ilbm",
    "replace_ilbm_palette",
    "remove_ilbm_cycle",
    "render_indexed_preview",
    "serialize_ilbm",
    "palette_at",
    "validate_cycles",
]
