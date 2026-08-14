"""Shared types for direct CustomPalette interchange codecs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from retropal.palettes.custom import CustomPalette, CustomPaletteError


class PaletteCodecError(CustomPaletteError):
    """Malformed input, unknown formats, or unsupported codec operations."""


@dataclass(frozen=True, slots=True)
class CodecInfo:
    id: str
    name: str
    extensions: tuple[str, ...]
    binary: bool
    preserves: tuple[str, ...]
    can_import: bool = True
    can_export: bool = True
    maximum_colors: int | None = None
    padded_color_count: int | None = None


@dataclass(frozen=True, slots=True)
class InterchangeReport:
    format_id: str
    messages: tuple[str, ...] = ()

    @property
    def lossless(self) -> bool:
        return not self.messages


@dataclass(frozen=True, slots=True)
class ImportResult:
    palette: CustomPalette
    report: InterchangeReport


@dataclass(frozen=True, slots=True)
class ExportResult:
    data: bytes
    report: InterchangeReport


class PaletteCodec(Protocol):
    info: CodecInfo

    def sniff(self, data: bytes) -> bool: ...

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult: ...

    def encode(self, palette: CustomPalette) -> ExportResult: ...


def metadata_loss(palette: CustomPalette, preserved: tuple[str, ...]) -> tuple[str, ...]:
    """Report populated model fields an external format cannot represent."""
    losses: list[str] = []
    if "id" not in preserved:
        losses.append("stable palette ID is not represented")
    if "name" not in preserved:
        losses.append("palette name is not represented")
    if palette.description and "description" not in preserved:
        losses.append("description is not represented")
    if palette.source and "source" not in preserved:
        losses.append("source/provenance is not represented")
    return tuple(losses)


def decode_text(data: bytes, format_name: str) -> str:
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PaletteCodecError(f"{format_name} input must be UTF-8 text") from exc
