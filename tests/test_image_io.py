from pathlib import Path

from PIL import Image

from retropal.core.image_io import inspect_image


def test_inspect_image(tmp_path: Path) -> None:
    path = tmp_path / "image.png"
    image = Image.new("RGBA", (2, 1))
    image.putdata([(255, 0, 0, 255), (0, 0, 255, 128)])
    image.save(path)
    info = inspect_image(path)
    assert info.width == 2
    assert info.height == 1
    assert info.unique_rgb_colors == 2
    assert info.has_alpha is True
