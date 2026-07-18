from pathlib import Path

import pytest
from PIL import Image

from retropal.core.models import DitherMode
from retropal.gui.controller import ConverterController


def test_controller_requires_source_image() -> None:
    controller = ConverterController()

    with pytest.raises(RuntimeError, match="No source image"):
        controller.refresh()


def test_controller_load_convert_and_export(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (4, 3), (220, 120, 40, 255)).save(source)
    controller = ConverterController()

    loaded = controller.load(source)
    controller.set_options("gameboy", DitherMode.NONE)
    converted = controller.refresh()
    output = controller.export(tmp_path / "result")

    assert loaded.size == (4, 3)
    assert converted.size == loaded.size
    assert output == tmp_path / "result.png"
    assert output.exists()
    assert controller.suggested_output_path() == tmp_path / "source-gameboy.png"


def test_controller_exports_palette(tmp_path) -> None:
    controller = ConverterController()
    source = tmp_path / "source.png"
    Image.new("RGBA", (2, 1), (15, 56, 15, 255)).save(source)
    controller.load(source)
    controller.set_options("gameboy", DitherMode.NONE)
    controller.refresh()
    output = controller.export_palette(tmp_path / "palette.gpl")
    assert output.exists()
    assert output.read_text(encoding="utf-8").startswith("GIMP Palette")
