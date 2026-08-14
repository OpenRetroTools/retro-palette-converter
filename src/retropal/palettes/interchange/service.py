"""Filesystem orchestration for palette interchange codecs."""

from __future__ import annotations

import re
from pathlib import Path

from retropal.palettes.custom import CustomPalette
from retropal.palettes.interchange.base import ExportResult, ImportResult, PaletteCodecError
from retropal.palettes.interchange.registry import codec_for_export, identify_codec
from retropal.palettes.validation import (
    ConversionPlan,
    ExecutionPolicy,
    execute_plan,
    plan_format_conversion,
)


def palette_id_from_path(path: Path) -> str:
    """Create a valid, deterministic proposed ID from an import filename."""
    stem = path.name
    for suffix in path.suffixes:
        stem = stem.removesuffix(suffix)
    normalized = re.sub(r"[^a-z0-9]+", "-", stem.casefold()).strip("-")
    if not normalized or not normalized[0].isalpha():
        normalized = f"palette-{normalized}".rstrip("-")
    return normalized


def import_palette(path: Path, *, format_id: str | None = None) -> ImportResult:
    try:
        data = path.read_bytes()
    except OSError:
        raise
    codec = identify_codec(path, data, format_id)
    palette_id = palette_id_from_path(path)
    return codec.decode(data, palette_id=palette_id, fallback_name=path.stem)


def export_palette(
    palette: CustomPalette,
    path: Path,
    *,
    format_id: str | None = None,
    overwrite: bool = False,
) -> ExportResult:
    if path.exists() and not overwrite:
        raise PaletteCodecError(f"Output already exists: {path}")
    codec = codec_for_export(path, format_id)
    result = codec.encode(palette)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(result.data)
    return result


def convert_palette(
    palette: CustomPalette,
    path: Path,
    *,
    format_id: str,
    policy: ExecutionPolicy | None = None,
    overwrite: bool = False,
    plan: ConversionPlan | None = None,
) -> ExportResult:
    """Explicitly execute a preflighted format conversion and write its bytes."""
    if path.exists() and not overwrite:
        raise PaletteCodecError(f"Output already exists: {path}")
    selected_plan = plan or plan_format_conversion(palette, format_id)
    if selected_plan.target_kind != "format" or selected_plan.target_id != format_id:
        raise PaletteCodecError("Conversion plan does not match target format")
    converted = execute_plan(palette, selected_plan, policy).palette
    codec = codec_for_export(path, format_id)
    result = codec.encode(converted)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(result.data)
    return result
