from pathlib import Path

from PIL import Image

from retropal.core.converter import convert, convert_file
from retropal.core.models import DitherMode
from retropal.palettes.fixed import load_fixed_palette


def test_fixed_palette_conversion_preserves_alpha() -> None:
    image = Image.new("RGBA", (2, 1))
    image.putdata([(255, 255, 255, 255), (20, 30, 40, 0)])
    result = convert(image, "gameboy")
    assert result.getpixel((1, 0))[3] == 0
    assert result.getpixel((0, 0))[:3] in load_fixed_palette("gameboy").colors


def test_floyd_steinberg_only_uses_palette_colors() -> None:
    image = Image.linear_gradient("L").resize((16, 16)).convert("RGBA")
    result = convert(image, "gameboy", DitherMode.FLOYD_STEINBERG)
    colors = {pixel[:3] for pixel in result.get_flattened_data()}
    assert colors <= set(load_fixed_palette("gameboy").colors)


def test_convert_file_writes_png(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    target = tmp_path / "nested" / "target.png"
    Image.new("RGB", (2, 2), "red").save(source)
    convert_file(source, target, "pico8", DitherMode.NONE)
    assert target.is_file()
    with Image.open(target) as result:
        assert result.format == "PNG"
        assert result.size == (2, 2)
