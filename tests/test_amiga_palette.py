from PIL import Image

from retropal.palettes.amiga_ocs import generate_ocs_palette, quantize_color_to_ocs


def test_quantize_color_uses_ocs_levels() -> None:
    assert quantize_color_to_ocs((1, 127, 254)) == (0, 119, 255)


def test_generated_palette_is_ocs_compatible() -> None:
    image = Image.new("RGB", (64, 1))
    image.putdata([(index * 4, 255 - index * 4, index * 3) for index in range(64)])
    palette = generate_ocs_palette(image, 16)
    assert 1 <= len(palette) <= 16
    assert all(channel % 17 == 0 for color in palette for channel in color)
