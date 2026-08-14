"""Shared indexed-image extraction workflow for CLI, GUI, and tests."""

from __future__ import annotations

from pathlib import Path

from retropal.palettes.custom import CustomPalette
from retropal.palettes.indexed.base import (
    IndexedPaletteError,
    IndexedPaletteResult,
    IndexedTransparency,
    usage_statistics,
)
from retropal.palettes.indexed.bmp import extract_bmp_structure
from retropal.palettes.indexed.gif import extract_gif_structure
from retropal.palettes.indexed.png import PNG_SIGNATURE, extract_png_structure
from retropal.palettes.interchange.service import palette_id_from_path

INDEXED_IMAGE_FORMATS = ("png", "gif", "bmp")


def _identify(data: bytes, requested: str | None) -> str:
    detected = (
        "png"
        if data.startswith(PNG_SIGNATURE)
        else "gif"
        if data.startswith((b"GIF87a", b"GIF89a"))
        else "bmp"
        if data.startswith(b"BM")
        else None
    )
    if requested is not None:
        normalized = requested.casefold()
        if normalized not in INDEXED_IMAGE_FORMATS:
            raise IndexedPaletteError(f"Unknown indexed image format: {requested}")
        if detected != normalized:
            raise IndexedPaletteError(
                f"File signature does not match requested {normalized.upper()} format"
            )
        return normalized
    if detected is None:
        raise IndexedPaletteError("File is not a recognized PNG, GIF, or BMP image")
    return detected


def extract_indexed_palette(
    path: Path,
    *,
    format_id: str | None = None,
    palette_id: str | None = None,
    name: str | None = None,
) -> IndexedPaletteResult:
    """Extract the complete stored palette table from one indexed image."""
    data = path.read_bytes()
    source_format = _identify(data, format_id)
    messages: list[str] = []
    transparency: IndexedTransparency | None = None
    frame_count = 1
    frame_index: int | None = None
    semantics_preserved = True
    if source_format == "png":
        structure = extract_png_structure(data)
        colors = structure.colors
        width, height, indexes = structure.width, structure.height, structure.used_indexes
        if structure.alpha is not None:
            transparency = IndexedTransparency(structure.alpha)
    elif source_format == "gif":
        structure = extract_gif_structure(data)
        colors = structure.colors
        width, height, indexes = structure.width, structure.height, structure.used_indexes
        frame_count = structure.frame_count
        frame_index = 0
        if structure.transparency_index is not None:
            alpha = [255] * len(colors)
            alpha[structure.transparency_index] = 0
            transparency = IndexedTransparency(tuple(alpha))
        if frame_count > 1:
            messages.append("GIF extraction uses the first image frame's effective color table.")
        if structure.distinct_frame_palettes:
            messages.append("Additional GIF frames use different effective color tables.")
            semantics_preserved = False
    else:
        structure = extract_bmp_structure(data)
        colors = structure.colors
        width, height, indexes = structure.width, structure.height, structure.used_indexes
        if structure.nonzero_reserved_entries:
            messages.append(
                "Non-zero BMP palette reserved bytes were ignored; "
                "BI_RGB does not define them as alpha."
            )
    used, unused, highest = usage_statistics(indexes, len(colors))
    if transparency is not None and transparency.non_opaque_indexes:
        messages.append(
            "Transparency is retained in this extraction report but native custom "
            "palettes store RGB only."
        )
    palette = CustomPalette(
        id=palette_id or palette_id_from_path(path),
        name=name or f"{path.stem} ({source_format.upper()} palette)",
        colors=colors,
        source=f"Indexed {source_format.upper()} palette extracted from {path.name}",
    )
    return IndexedPaletteResult(
        palette=palette,
        source_format=source_format,
        stored_entry_count=len(colors),
        width=width,
        height=height,
        used_indexes=used,
        unused_indexes=unused,
        highest_used_index=highest,
        transparency=transparency,
        frame_index=frame_index,
        frame_count=frame_count,
        messages=tuple(messages),
        all_stored_semantics_preserved=semantics_preserved,
    )
