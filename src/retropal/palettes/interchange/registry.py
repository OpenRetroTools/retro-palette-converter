"""Shared palette codec registry and safe format discovery."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from retropal.palettes.interchange.act import CODEC as ACT
from retropal.palettes.interchange.base import PaletteCodec, PaletteCodecError
from retropal.palettes.interchange.csv_codec import CODEC as CSV
from retropal.palettes.interchange.gpl import CODEC as GPL
from retropal.palettes.interchange.jasc import CODEC as JASC
from retropal.palettes.interchange.json_codec import CODEC as JSON
from retropal.palettes.interchange.riff import CODEC as RIFF_PAL

CODECS: tuple[PaletteCodec, ...] = (GPL, JASC, RIFF_PAL, ACT, JSON, CSV)
_INTENTIONALLY_AMBIGUOUS_EXTENSIONS = frozenset({".pal"})
_BY_ID: dict[str, PaletteCodec] = {}
_BY_EXTENSION: dict[str, tuple[PaletteCodec, ...]] = {}


def _index_codecs(codecs: tuple[PaletteCodec, ...]) -> None:
    extensions: defaultdict[str, list[PaletteCodec]] = defaultdict(list)
    for codec in codecs:
        if codec.info.id in _BY_ID:
            raise RuntimeError(f"Duplicate palette codec ID: {codec.info.id}")
        _BY_ID[codec.info.id] = codec
        for extension in codec.info.extensions:
            if not extension.startswith(".") or extension != extension.lower():
                raise RuntimeError(f"Invalid codec extension: {extension}")
            extensions[extension].append(codec)
    _BY_EXTENSION.update(
        (extension, tuple(candidates)) for extension, candidates in extensions.items()
    )
    unexpected = tuple(
        extension
        for extension, candidates in _BY_EXTENSION.items()
        if len(candidates) > 1 and extension not in _INTENTIONALLY_AMBIGUOUS_EXTENSIONS
    )
    if unexpected:
        raise RuntimeError(f"Duplicate palette codec extensions: {', '.join(unexpected)}")


_index_codecs(CODECS)


def get_codec(codec_id: str) -> PaletteCodec:
    try:
        return _BY_ID[codec_id]
    except KeyError as exc:
        raise PaletteCodecError(f"Unknown palette format: {codec_id}") from exc


def identify_codec(path: Path, data: bytes, format_id: str | None = None) -> PaletteCodec:
    """Identify an import using an override or positive, unambiguous sniffing."""
    if format_id is not None:
        codec = get_codec(format_id)
        if not codec.sniff(data):
            raise PaletteCodecError(f"Input does not match requested {codec.info.name} format")
        return codec
    candidates = _BY_EXTENSION.get(path.suffix.lower())
    if candidates is None:
        raise PaletteCodecError(
            f"Unsupported palette extension: {path.suffix or '(none)'}; use --format"
        )
    matches = tuple(codec for codec in candidates if codec.sniff(data))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise PaletteCodecError(f"Could not identify palette format for {path.name}; use --format")
    raise PaletteCodecError(
        "Ambiguous palette format: " + ", ".join(codec.info.id for codec in matches)
    )


def codec_for_export(path: Path, format_id: str | None = None) -> PaletteCodec:
    if format_id is not None:
        return get_codec(format_id)
    candidates = _BY_EXTENSION.get(path.suffix.lower(), ())
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        raise PaletteCodecError(f"Unsupported palette extension: {path.suffix or '(none)'}")
    raise PaletteCodecError(
        f"Extension {path.suffix} is ambiguous; select one of: "
        + ", ".join(codec.info.id for codec in candidates)
    )


def iter_codecs() -> tuple[PaletteCodec, ...]:
    return CODECS
