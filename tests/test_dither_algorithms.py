from __future__ import annotations

import pytest
from PIL import Image

from retropal.core.dither import get_dither

BLACK_AND_WHITE = ((0, 0, 0), (255, 255, 255))
MEDIUM_PALETTE = tuple((value, value, value) for value in range(0, 256, 32))
LARGE_PALETTE = tuple(
    (red, green, blue)
    for red in (0, 85, 170, 255)
    for green in (0, 85, 170, 255)
    for blue in (0, 255)
)


def _gray_image(width: int, height: int, value: int = 128) -> Image.Image:
    return Image.new("RGBA", (width, height), (value, value, value, 255))


def test_atkinson_is_deterministic_and_uses_palette() -> None:
    algorithm = get_dither("atkinson")
    first = algorithm.apply(_gray_image(8, 8), BLACK_AND_WHITE)
    second = algorithm.apply(_gray_image(8, 8), BLACK_AND_WHITE)

    assert list(first.get_flattened_data()) == list(second.get_flattened_data())
    assert {pixel[:3] for pixel in first.get_flattened_data()} <= set(BLACK_AND_WHITE)
    assert len({pixel[:3] for pixel in first.get_flattened_data()}) == 2


def test_bayer_algorithms_create_repeatable_patterns() -> None:
    for dither_id, size in (
        ("bayer-2x2", 2),
        ("bayer-4x4", 4),
        ("bayer-8x8", 8),
    ):
        algorithm = get_dither(dither_id)
        result = algorithm.apply(_gray_image(size * 2, size * 2), BLACK_AND_WHITE)
        pixels = result.load()

        for y in range(size):
            for x in range(size):
                assert pixels[x, y] == pixels[x + size, y]
                assert pixels[x, y] == pixels[x, y + size]

        assert {pixel[:3] for pixel in result.get_flattened_data()} == set(BLACK_AND_WHITE)


def test_new_dithers_preserve_transparency() -> None:
    image = Image.new("RGBA", (1, 1), (128, 128, 128, 0))

    for dither_id in ("atkinson", "bayer-2x2", "bayer-4x4", "bayer-8x8"):
        result = get_dither(dither_id).apply(image, BLACK_AND_WHITE)
        assert result.getpixel((0, 0)) == (0, 0, 0, 0)


@pytest.mark.parametrize("dither_id", ["bayer-2x2", "bayer-4x4", "bayer-8x8", "floyd-steinberg"])
@pytest.mark.parametrize("palette", [BLACK_AND_WHITE, MEDIUM_PALETTE, LARGE_PALETTE])
def test_representative_dithers_preserve_shape_alpha_and_palette(
    dither_id: str,
    palette: tuple[tuple[int, int, int], ...],
) -> None:
    image = Image.new("RGBA", (5, 3))
    image.putdata(
        [
            (x * 47, y * 83, (x + y) * 31, 0 if (x, y) == (2, 1) else 64 + x * 40)
            for y in range(image.height)
            for x in range(image.width)
        ]
    )
    algorithm = get_dither(dither_id)

    first = algorithm.apply(image, palette)
    second = algorithm.apply(image, palette)

    assert first.mode == "RGBA"
    assert first.size == image.size
    assert list(first.get_flattened_data()) == list(second.get_flattened_data())
    assert {pixel[:3] for pixel in first.get_flattened_data() if pixel[3] > 0} <= set(palette)
    assert [pixel[3] for pixel in first.get_flattened_data()] == [
        pixel[3] for pixel in image.get_flattened_data()
    ]
    assert first.getpixel((2, 1)) == (0, 0, 0, 0)


def test_bayer_2x2_tiny_fixture_has_known_output() -> None:
    image = Image.new("RGBA", (2, 2))
    image.putdata(
        [
            (96, 96, 96, 255),
            (128, 128, 128, 255),
            (160, 160, 160, 255),
            (128, 128, 128, 128),
        ]
    )

    result = get_dither("bayer-2x2").apply(image, BLACK_AND_WHITE)

    assert list(result.get_flattened_data()) == [
        (0, 0, 0, 255),
        (255, 255, 255, 255),
        (255, 255, 255, 255),
        (0, 0, 0, 128),
    ]
