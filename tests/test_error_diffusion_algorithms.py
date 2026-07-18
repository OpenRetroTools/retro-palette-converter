from __future__ import annotations

from PIL import Image

from retropal.core.dither import get_dither

BLACK_AND_WHITE = ((0, 0, 0), (255, 255, 255))
NEW_ERROR_DIFFUSION_IDS = (
    "sierra-lite",
    "sierra",
    "burkes",
    "stucki",
    "jarvis-judice-ninke",
)


def _gradient(width: int = 16, height: int = 8) -> Image.Image:
    image = Image.new("RGBA", (width, height))
    image.putdata(
        [
            (value, value, value, 255)
            for _y in range(height)
            for x in range(width)
            for value in [round(255 * x / (width - 1))]
        ]
    )
    return image


def test_error_diffusion_algorithms_are_deterministic_and_use_palette() -> None:
    image = _gradient()

    for dither_id in NEW_ERROR_DIFFUSION_IDS:
        algorithm = get_dither(dither_id)
        first = algorithm.apply(image, BLACK_AND_WHITE)
        second = algorithm.apply(image, BLACK_AND_WHITE)

        assert list(first.get_flattened_data()) == list(second.get_flattened_data())
        assert {pixel[:3] for pixel in first.get_flattened_data()} == set(BLACK_AND_WHITE)


def test_error_diffusion_algorithms_preserve_alpha() -> None:
    image = Image.new("RGBA", (3, 1))
    image.putdata(
        [
            (128, 128, 128, 255),
            (128, 128, 128, 0),
            (128, 128, 128, 128),
        ]
    )

    for dither_id in NEW_ERROR_DIFFUSION_IDS:
        result = get_dither(dither_id).apply(image, BLACK_AND_WHITE)
        assert result.getpixel((0, 0))[3] == 255
        assert result.getpixel((1, 0)) == (0, 0, 0, 0)
        assert result.getpixel((2, 0))[3] == 128
