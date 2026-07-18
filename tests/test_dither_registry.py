from __future__ import annotations

import pytest
from PIL import Image

from retropal.core.dither import DITHER_IDS, DitherAlgorithm, get_dither, iter_dithers
from retropal.palettes.fixed import load_fixed_palette


def test_builtin_dithers_are_registered_in_stable_order() -> None:
    assert DITHER_IDS == (
        "none",
        "floyd-steinberg",
        "atkinson",
        "bayer-2x2",
        "bayer-4x4",
        "bayer-8x8",
        "sierra-lite",
        "sierra",
        "burkes",
        "stucki",
        "jarvis-judice-ninke",
    )
    assert [algorithm.display_name for algorithm in iter_dithers()] == [
        "None",
        "Floyd–Steinberg",
        "Atkinson",
        "Bayer 2×2",
        "Bayer 4×4",
        "Bayer 8×8",
        "Sierra Lite",
        "Sierra",
        "Burkes",
        "Stucki",
        "Jarvis–Judice–Ninke",
    ]


def test_get_dither_returns_algorithm() -> None:
    algorithm = get_dither("none")
    assert isinstance(algorithm, DitherAlgorithm)
    assert algorithm.id == "none"


def test_get_dither_rejects_unknown_id() -> None:
    with pytest.raises(ValueError, match="Unsupported dithering mode"):
        get_dither("unknown")


def test_registered_algorithms_preserve_alpha_and_use_palette_colors() -> None:
    image = Image.new("RGBA", (2, 1))
    image.putdata([(210, 120, 40, 255), (20, 30, 40, 0)])
    palette = load_fixed_palette("gameboy").colors

    for algorithm in iter_dithers():
        result = algorithm.apply(image, palette)
        assert result.getpixel((1, 0))[3] == 0
        assert result.getpixel((0, 0))[:3] in palette
