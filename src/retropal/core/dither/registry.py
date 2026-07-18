"""Registry for dithering algorithms."""

from __future__ import annotations

from collections.abc import Iterable

from retropal.core.dither.base import DitherAlgorithm

_REGISTRY: dict[str, DitherAlgorithm] = {}


def register(algorithm: DitherAlgorithm) -> None:
    """Register a dithering algorithm by its stable identifier."""

    if not algorithm.id:
        raise ValueError("Dither algorithm id must not be empty")
    if algorithm.id in _REGISTRY:
        raise ValueError(f"Dither algorithm already registered: {algorithm.id}")
    _REGISTRY[algorithm.id] = algorithm


def get_dither(dither_id: str) -> DitherAlgorithm:
    """Return a registered dithering algorithm."""

    try:
        return _REGISTRY[dither_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported dithering mode: {dither_id}") from exc


def iter_dithers() -> Iterable[DitherAlgorithm]:
    """Iterate over algorithms in registration order."""

    return tuple(_REGISTRY.values())


def list_dithers() -> tuple[str, ...]:
    """Return all registered stable identifiers."""

    return tuple(_REGISTRY)
