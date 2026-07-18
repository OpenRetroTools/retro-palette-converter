"""Extensible dithering algorithm registry."""

from __future__ import annotations

from retropal.core.dither.atkinson import ALGORITHM as ATKINSON
from retropal.core.dither.base import DitherAlgorithm
from retropal.core.dither.error_diffusion import (
    BURKES_ALGORITHM,
    JARVIS_JUDICE_NINKE_ALGORITHM,
    SIERRA_ALGORITHM,
    SIERRA_LITE_ALGORITHM,
    STUCKI_ALGORITHM,
)
from retropal.core.dither.floyd_steinberg import ALGORITHM as FLOYD_STEINBERG
from retropal.core.dither.none import ALGORITHM as NONE
from retropal.core.dither.ordered import (
    BAYER_2_ALGORITHM,
    BAYER_4_ALGORITHM,
    BAYER_8_ALGORITHM,
)
from retropal.core.dither.registry import get_dither, iter_dithers, list_dithers, register

register(NONE)
register(FLOYD_STEINBERG)
register(ATKINSON)
register(BAYER_2_ALGORITHM)
register(BAYER_4_ALGORITHM)
register(BAYER_8_ALGORITHM)
register(SIERRA_LITE_ALGORITHM)
register(SIERRA_ALGORITHM)
register(BURKES_ALGORITHM)
register(STUCKI_ALGORITHM)
register(JARVIS_JUDICE_NINKE_ALGORITHM)

DITHER_IDS = list_dithers()

# Compatibility aliases retained for callers of the pre-M2.2 API.
map_without_dither = NONE.apply
map_floyd_steinberg = FLOYD_STEINBERG.apply

__all__ = [
    "DITHER_IDS",
    "DitherAlgorithm",
    "get_dither",
    "iter_dithers",
    "list_dithers",
    "map_floyd_steinberg",
    "map_without_dither",
    "register",
]
