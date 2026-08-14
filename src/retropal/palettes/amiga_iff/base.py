"""Typed IFF/ILBM palette document and report models.

Field layouts follow EA IFF 85 and Commodore's ILBM specification. Multi-byte
values are big-endian; odd payloads have one alignment byte outside ckSize.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from retropal.palettes.custom import CustomPalette, CustomPaletteError


class IlbmPaletteError(CustomPaletteError):
    """Malformed, unsupported, or unsafe ILBM palette operation."""


@dataclass(frozen=True, slots=True)
class IffChunk:
    """One ordered IFF chunk, including its original alignment byte."""

    id: bytes
    payload: bytes
    pad_byte: bytes = b""

    def __post_init__(self) -> None:
        if len(self.id) != 4:
            raise IlbmPaletteError("IFF chunk IDs must contain exactly four bytes")
        expected_pad = 1 if len(self.payload) % 2 else 0
        if len(self.pad_byte) != expected_pad:
            raise IlbmPaletteError("IFF chunk alignment byte does not match payload length")


@dataclass(frozen=True, slots=True)
class ColorCycleRange:
    """Parsed Deluxe Paint CRNG values plus raw bytes for faithful rewriting."""

    rate: int
    flags: int
    low: int
    high: int
    reserved: int
    raw_payload: bytes

    @property
    def enabled(self) -> bool:
        return bool(self.flags & 1)

    @property
    def reversed(self) -> bool:
        return bool(self.flags & 2)


@dataclass(frozen=True, slots=True)
class IlbmDocument:
    """An ILBM FORM with all chunks retained in original order."""

    form_type: bytes
    chunks: tuple[IffChunk, ...]
    palette: CustomPalette | None
    color_cycles: tuple[ColorCycleRange, ...]
    effective_cmap_index: int | None
    source: str | None = None

    def with_palette(self, palette: CustomPalette) -> IlbmDocument:
        """Replace the effective CMAP, or insert one immediately before BODY."""
        payload = bytes(channel for color in palette.colors for channel in color)
        cmap = IffChunk(b"CMAP", payload, b"\0" if len(payload) % 2 else b"")
        chunks = list(self.chunks)
        if self.effective_cmap_index is not None:
            chunks[self.effective_cmap_index] = cmap
            index = self.effective_cmap_index
        else:
            index = next(
                (position for position, chunk in enumerate(chunks) if chunk.id == b"BODY"),
                len(chunks),
            )
            chunks.insert(index, cmap)
        return replace(self, chunks=tuple(chunks), palette=palette, effective_cmap_index=index)


@dataclass(frozen=True, slots=True)
class IlbmImportResult:
    document: IlbmDocument
    palette: CustomPalette
    messages: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IlbmWriteResult:
    data: bytes
    messages: tuple[str, ...]
