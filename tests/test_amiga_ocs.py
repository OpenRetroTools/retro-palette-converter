import pytest

from retropal.palettes.amiga_ocs import quantize_channel_to_4bit


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (0, 0),
        (8, 0),
        (9, 17),
        (127, 119),
        (128, 136),
        (255, 255),
    ],
)
def test_quantize_channel_to_4bit(source: int, expected: int) -> None:
    assert quantize_channel_to_4bit(source) == expected


@pytest.mark.parametrize("source", [-1, 256])
def test_quantize_channel_rejects_invalid_values(source: int) -> None:
    with pytest.raises(ValueError):
        quantize_channel_to_4bit(source)
