"""Conservative import-only support for verified Brilliance palette documents.

The supported structure is based on Digital Creations' manual and seventeen
Brilliance 1.0/2.0 samples from Aminet ArcsPack 12. Export is intentionally
unsupported because the 128 gradient slots and Brilliance-specific range
chunks do not have a sufficiently documented writer contract.
"""

from __future__ import annotations

from retropal.palettes.amiga_iff import IlbmDocument, IlbmPaletteError, parse_ilbm
from retropal.palettes.custom import CustomPalette
from retropal.palettes.interchange.base import (
    CodecInfo,
    ExportResult,
    ImportResult,
    InterchangeReport,
    PaletteCodecError,
)

_ANNOTATIONS = {
    b"Written by Brilliance 1.0": "1.0",
    b"Written by Brilliance Release 2.0 ": "2.0",
}
_PALETTE_ENTRIES = 256
_GRADIENT_ENTRIES = 128
_CMAP_ENTRIES = _PALETTE_ENTRIES + _GRADIENT_ENTRIES
_CMAP_BYTES = _CMAP_ENTRIES * 3
_SUPPORTED_CHUNKS = frozenset({b"ANNO", b"CMAP", b"DRNG", b"CRNG", b"BRNG"})


class BrilliancePltCodec:
    info = CodecInfo(
        id="brilliance-plt",
        name="Brilliance palette (verified ILBM variant)",
        extensions=(".plt",),
        binary=True,
        preserves=("colors",),
        can_export=False,
    )

    def sniff(self, data: bytes) -> bool:
        try:
            self._validated_document(data)
        except PaletteCodecError:
            return False
        return True

    @staticmethod
    def _validated_document(data: bytes) -> tuple[IlbmDocument, str]:
        try:
            document = parse_ilbm(data)
        except IlbmPaletteError as exc:
            raise PaletteCodecError(f"Malformed Brilliance palette: {exc}") from exc
        if len(document.chunks) < 2:
            raise PaletteCodecError("Unsupported Brilliance palette structure")
        annotation, cmap = document.chunks[:2]
        if annotation.id != b"ANNO" or annotation.payload not in _ANNOTATIONS:
            raise PaletteCodecError("Missing verified Brilliance 1.0/2.0 ANNO signature")
        if cmap.id != b"CMAP" or len(cmap.payload) != _CMAP_BYTES:
            raise PaletteCodecError(
                f"Brilliance CMAP must contain exactly {_CMAP_ENTRIES} RGB entries"
            )
        unsupported = tuple(
            chunk.id.decode("ascii", "replace")
            for chunk in document.chunks
            if chunk.id not in _SUPPORTED_CHUNKS
        )
        if unsupported:
            raise PaletteCodecError(
                "Unsupported Brilliance palette chunks: " + ", ".join(unsupported)
            )
        return document, _ANNOTATIONS[annotation.payload]

    def decode(self, data: bytes, *, palette_id: str, fallback_name: str) -> ImportResult:
        document, version = self._validated_document(data)
        cmap = document.chunks[1].payload
        palette_data = cmap[: _PALETTE_ENTRIES * 3]
        colors = tuple(
            (palette_data[index], palette_data[index + 1], palette_data[index + 2])
            for index in range(0, len(palette_data), 3)
        )
        messages = [
            "Brilliance files do not record the active register count; all 256 stored "
            "register slots were imported.",
            "The 128 Brilliance gradient slots are outside CustomPalette and were not imported.",
        ]
        extra_ids = tuple(chunk.id.decode("ascii") for chunk in document.chunks[2:])
        if extra_ids:
            messages.append(
                "Brilliance gradient/cycle chunks are not represented: " + ", ".join(extra_ids)
            )
        if all(channel % 17 == 0 for color in colors for channel in color):
            messages.append(
                "Stored RGB bytes are consistent with 4-bit-expanded pre-AGA colours; "
                "bytes were retained exactly without normalization."
            )
        palette = CustomPalette(
            palette_id,
            fallback_name,
            colors,
            source=f"Imported from verified Brilliance {version} palette document",
        )
        return ImportResult(palette, InterchangeReport(self.info.id, tuple(messages)))

    def encode(self, palette: CustomPalette) -> ExportResult:
        del palette
        raise PaletteCodecError(
            "Brilliance palette export is not supported: gradient serialization is undocumented"
        )


CODEC = BrilliancePltCodec()
