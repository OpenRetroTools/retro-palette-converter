from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from retropal import __version__
from retropal.cli import build_parser, main
from retropal.core.dither import DITHER_IDS


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


def test_gui_command_delegates_to_application(monkeypatch, capsys) -> None:
    import retropal.application

    monkeypatch.setattr(retropal.application, "run_gui", lambda: 17)
    assert main(["gui"]) == 17
    assert capsys.readouterr().out == ""


def test_batch_command_converts_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    Image.new("RGBA", (2, 2), (100, 150, 200, 255)).save(source_dir / "image.png")

    assert main(["batch", str(source_dir), str(target_dir), "--palette", "ega"]) == 0

    assert (target_dir / "image.png").exists()
    assert "Summary: converted=1 skipped=0 failed=0" in capsys.readouterr().out


def test_batch_command_dry_run_and_no_recursive(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    nested = source_dir / "nested"
    nested.mkdir(parents=True)
    Image.new("RGBA", (2, 2), (100, 150, 200, 255)).save(nested / "image.png")

    assert (
        main(
            [
                "batch",
                str(source_dir),
                str(target_dir),
                "--palette",
                "ega",
                "--dry-run",
                "--no-recursive",
            ]
        )
        == 0
    )

    assert not target_dir.exists()
    assert "Summary: converted=0 skipped=0 failed=0" in capsys.readouterr().out


def test_cli_dither_choices_come_from_registry() -> None:
    parser = build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if action.dest == "command"  # noqa: SLF001
    )
    convert_parser = subparsers.choices["convert"]
    dither_action = next(action for action in convert_parser._actions if action.dest == "dither")
    assert tuple(dither_action.choices) == DITHER_IDS


def test_palettes_verbose_command(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["palettes", "--verbose"]) == 0
    output = capsys.readouterr().out
    assert "commodore-64: Commodore 64 (VICE)" in output
    assert "amiga-aga-256: Amiga AGA 256" in output
    assert "Manufacturer: Commodore" in output


def test_palettes_family_filter(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["palettes", "--family", "Atari"]) == 0
    output = capsys.readouterr().out.split()
    assert set(output) == {
        "atari-2600-tia",
        "atari-8bit-antic-gtia",
        "atari-st",
        "atari-ste",
        "atari-falcon030",
    }


def test_palettes_family_filter_is_case_insensitive(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["palettes", "--family", "atari"]) == 0
    output = capsys.readouterr().out
    assert "atari-falcon030" in output


def test_palettes_family_filter_verbose(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["palettes", "--family", "Atari", "--verbose"]) == 0
    output = capsys.readouterr().out
    assert "atari-st: Atari ST" in output
    assert "Family: Atari" in output
    assert "commodore-64" not in output
