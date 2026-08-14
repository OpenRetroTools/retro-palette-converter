"""Filesystem workflows for ILBM inspection, CMAP import, and safe replacement."""

from __future__ import annotations

from pathlib import Path

from retropal.palettes.amiga_iff.base import (
    ColorCycleRange,
    IlbmDocument,
    IlbmImportResult,
    IlbmPaletteError,
    IlbmWriteResult,
)
from retropal.palettes.amiga_iff.cycling import CycleIssueSeverity, validate_cycles
from retropal.palettes.amiga_iff.parser import load_ilbm_document, serialize_ilbm
from retropal.palettes.custom import CustomPalette
from retropal.palettes.interchange.service import palette_id_from_path


def inspect_ilbm(path: Path) -> IlbmDocument:
    """Load an ILBM for metadata inspection using deterministic defaults."""
    return load_ilbm_document(
        path,
        palette_id=palette_id_from_path(path),
        palette_name=f"{path.stem} (ILBM CMAP)",
    )


def import_ilbm_palette(
    path: Path,
    *,
    palette_id: str | None = None,
    name: str | None = None,
) -> IlbmImportResult:
    document = load_ilbm_document(
        path,
        palette_id=palette_id or palette_id_from_path(path),
        palette_name=name or f"{path.stem} (ILBM CMAP)",
    )
    if document.palette is None:
        raise IlbmPaletteError("ILBM contains no CMAP palette")
    messages = [
        "ILBM chunk structure and non-CMAP payloads are not stored in the native "
        "RGB palette document."
    ]
    if sum(chunk.id == b"CMAP" for chunk in document.chunks) > 1:
        messages.append("Multiple CMAP chunks found; the last CMAP before BODY is effective.")
    if document.color_cycles:
        messages.append(
            "CRNG colour-cycle metadata is not stored in the native RGB palette document."
        )
    return IlbmImportResult(document, document.palette, tuple(messages))


def replace_ilbm_palette(
    source: Path,
    output: Path,
    palette: CustomPalette,
    *,
    overwrite: bool = False,
) -> IlbmWriteResult:
    if output.exists() and not overwrite:
        raise IlbmPaletteError(f"Output already exists: {output}")
    document = inspect_ilbm(source)
    updated = document.with_palette(palette)
    data = serialize_ilbm(updated)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    action = "replaced" if document.effective_cmap_index is not None else "inserted before BODY"
    return IlbmWriteResult(
        data,
        (f"CMAP was {action}; all other chunk payloads and ordering were preserved.",),
    )


def write_cycle_document(
    document: IlbmDocument,
    output: Path,
    *,
    overwrite: bool = False,
) -> IlbmWriteResult:
    if output.exists() and not overwrite:
        raise IlbmPaletteError(f"Output already exists: {output}")
    palette_size = len(document.palette.colors) if document.palette is not None else 0
    issues = validate_cycles(document.color_cycles, palette_size)
    blocking = tuple(issue for issue in issues if issue.severity is CycleIssueSeverity.BLOCKING)
    if blocking:
        raise IlbmPaletteError("; ".join(issue.message for issue in blocking))
    data = serialize_ilbm(document)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return IlbmWriteResult(
        data,
        ("CRNG changes written; CMAP, BODY, unknown chunks, and ordering were preserved.",),
    )


def edit_ilbm_cycle(
    source: Path,
    output: Path,
    cycle_index: int,
    cycle: ColorCycleRange,
    *,
    overwrite: bool = False,
) -> IlbmWriteResult:
    return write_cycle_document(
        inspect_ilbm(source).with_cycle_replaced(cycle_index, cycle),
        output,
        overwrite=overwrite,
    )


def add_ilbm_cycle(
    source: Path,
    output: Path,
    cycle: ColorCycleRange,
    *,
    overwrite: bool = False,
) -> IlbmWriteResult:
    return write_cycle_document(
        inspect_ilbm(source).with_cycle_added(cycle), output, overwrite=overwrite
    )


def remove_ilbm_cycle(
    source: Path,
    output: Path,
    cycle_index: int,
    *,
    overwrite: bool = False,
) -> IlbmWriteResult:
    return write_cycle_document(
        inspect_ilbm(source).with_cycle_removed(cycle_index), output, overwrite=overwrite
    )
