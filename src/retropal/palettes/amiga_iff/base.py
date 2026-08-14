"""Typed IFF/ILBM palette document and report models.

Field layouts follow EA IFF 85 and Commodore's ILBM specification. Multi-byte
values are big-endian; odd payloads have one alignment byte outside ckSize.
"""

from __future__ import annotations

import struct
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

    def __post_init__(self) -> None:
        if not 0 <= self.reserved <= 0xFFFF:
            raise IlbmPaletteError("CRNG reserved value must fit an unsigned word")
        if not 0 <= self.rate <= 0xFFFF:
            raise IlbmPaletteError("CRNG rate must fit an unsigned word")
        if not 0 <= self.flags <= 0xFFFF:
            raise IlbmPaletteError("CRNG flags must fit an unsigned word")
        if not 0 <= self.low <= 0xFF or not 0 <= self.high <= 0xFF:
            raise IlbmPaletteError("CRNG indexes must fit an unsigned byte")
        if self.low > self.high:
            raise IlbmPaletteError("CRNG low index must not exceed high index")
        if len(self.raw_payload) != 8:
            raise IlbmPaletteError("CRNG raw payload must contain exactly 8 bytes")

    @property
    def enabled(self) -> bool:
        return bool(self.flags & 1)

    @property
    def reversed(self) -> bool:
        return bool(self.flags & 2)

    @property
    def steps_per_second(self) -> float:
        return self.rate * 60 / 16384

    @property
    def seconds_per_step(self) -> float | None:
        return 16384 / (self.rate * 60) if self.rate else None

    @property
    def range_length(self) -> int:
        return self.high - self.low + 1

    def edited(
        self,
        *,
        rate: int | None = None,
        low: int | None = None,
        high: int | None = None,
        active: bool | None = None,
        reverse: bool | None = None,
    ) -> ColorCycleRange:
        """Return a rewritten range while retaining reserved and unknown flag bits."""
        flags = self.flags
        if active is not None:
            flags = flags | 1 if active else flags & ~1
        if reverse is not None:
            flags = flags | 2 if reverse else flags & ~2
        values = (
            self.reserved,
            self.rate if rate is None else rate,
            flags,
            self.low if low is None else low,
            self.high if high is None else high,
        )
        candidate = ColorCycleRange(
            values[1], values[2], values[3], values[4], values[0], b"\0" * 8
        )
        return replace(candidate, raw_payload=struct.pack(">HHHBB", *values))

    @classmethod
    def create(
        cls,
        *,
        rate: int,
        low: int,
        high: int,
        active: bool = True,
        reverse: bool = False,
    ) -> ColorCycleRange:
        flags = (1 if active else 0) | (2 if reverse else 0)
        candidate = cls(rate, flags, low, high, 0, b"\0" * 8)
        return replace(candidate, raw_payload=struct.pack(">HHHBB", 0, rate, flags, low, high))


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

    def with_cycle_replaced(self, cycle_index: int, cycle: ColorCycleRange) -> IlbmDocument:
        chunk_indexes = [index for index, chunk in enumerate(self.chunks) if chunk.id == b"CRNG"]
        if not 0 <= cycle_index < len(chunk_indexes):
            raise IlbmPaletteError(f"CRNG index out of range: {cycle_index}")
        chunks = list(self.chunks)
        chunks[chunk_indexes[cycle_index]] = IffChunk(b"CRNG", cycle.raw_payload)
        cycles = list(self.color_cycles)
        cycles[cycle_index] = cycle
        return replace(self, chunks=tuple(chunks), color_cycles=tuple(cycles))

    def with_cycle_removed(self, cycle_index: int) -> IlbmDocument:
        chunk_indexes = [index for index, chunk in enumerate(self.chunks) if chunk.id == b"CRNG"]
        if not 0 <= cycle_index < len(chunk_indexes):
            raise IlbmPaletteError(f"CRNG index out of range: {cycle_index}")
        chunks = list(self.chunks)
        chunks.pop(chunk_indexes[cycle_index])
        cycles = self.color_cycles[:cycle_index] + self.color_cycles[cycle_index + 1 :]
        return replace(self, chunks=tuple(chunks), color_cycles=cycles)

    def with_cycle_added(self, cycle: ColorCycleRange) -> IlbmDocument:
        chunks = list(self.chunks)
        existing = [index for index, chunk in enumerate(chunks) if chunk.id == b"CRNG"]
        if existing:
            insertion = existing[-1] + 1
        else:
            insertion = next(
                (index for index, chunk in enumerate(chunks) if chunk.id == b"BODY"), len(chunks)
            )
        chunks.insert(insertion, IffChunk(b"CRNG", cycle.raw_payload))
        return replace(
            self,
            chunks=tuple(chunks),
            color_cycles=(*self.color_cycles, cycle),
            effective_cmap_index=(
                self.effective_cmap_index + 1
                if self.effective_cmap_index is not None and insertion <= self.effective_cmap_index
                else self.effective_cmap_index
            ),
        )


@dataclass(frozen=True, slots=True)
class IlbmImportResult:
    document: IlbmDocument
    palette: CustomPalette
    messages: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class IlbmWriteResult:
    data: bytes
    messages: tuple[str, ...]
