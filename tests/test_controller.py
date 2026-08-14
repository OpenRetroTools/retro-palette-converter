from pathlib import Path

import pytest
from PIL import Image

from retropal.core.models import DitherMode
from retropal.gui import controller as controller_module
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


def test_refresh_resolves_adaptive_palette_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.png"
    Image.new("RGBA", (3, 2), (120, 80, 40, 255)).save(source)
    resolved = ((0, 0, 0), (255, 255, 255))
    calls = 0

    def resolve_once(palette_id: str, image: Image.Image) -> tuple[tuple[int, int, int], ...]:
        nonlocal calls
        calls += 1
        assert palette_id == "amiga-ocs-16"
        assert image.size == (3, 2)
        return resolved

    monkeypatch.setattr(controller_module, "palette_colors", resolve_once)
    controller = ConverterController()
    controller.load(source)
    controller.set_options("amiga-ocs-16", DitherMode.NONE)

    controller.refresh()

    assert calls == 1
    assert controller.display_palette == resolved
    assert set(controller.result_palette) <= set(resolved)
