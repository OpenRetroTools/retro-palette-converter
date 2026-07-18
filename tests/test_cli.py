from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from retropal import __version__
from retropal.cli import main


def test_cli_without_arguments_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "Convert images to retro color palettes" in capsys.readouterr().out


def test_version_option(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert f"Retro Palette Converter {__version__}" in capsys.readouterr().out


def test_palettes_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["palettes"]) == 0
    output = capsys.readouterr().out
    assert "gameboy" in output
    assert "amiga-ocs-32" in output


def test_convert_and_inspect_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "source.png"
    target = tmp_path / "target.png"
    Image.new("RGBA", (3, 2), (200, 100, 50, 255)).save(source)
    assert main(["convert", str(source), "--palette", "ega", "-o", str(target)]) == 0
    assert target.exists()
    assert main(["inspect", str(target)]) == 0
    assert "Dimensions: 3x2" in capsys.readouterr().out
