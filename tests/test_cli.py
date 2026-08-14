from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from retropal import __version__
from retropal.cli import build_parser, main
from retropal.core.dither import DITHER_IDS
from retropal.palettes.native import load_native_palette
from tests.indexed_image_fixtures import indexed_bmp, indexed_gif, indexed_png


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


def test_custom_palette_cli_workflow_and_conversion(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    store = tmp_path / "palettes"
    common = ["custom-palettes", "--store", str(store)]
    assert main([*common, "create", "cli-demo", "CLI Demo", "#000000", "#FFFFFF", "#000000"]) == 0
    assert main([*common, "rename", "cli-demo", "Renamed Demo"]) == 0
    assert main([*common, "add", "cli-demo", "#FF0000"]) == 0
    assert main([*common, "set", "cli-demo", "1", "#00FF00"]) == 0
    assert main([*common, "move", "cli-demo", "3", "1"]) == 0
    assert main([*common, "remove", "cli-demo", "2"]) == 0
    assert main([*common, "show", "cli-demo"]) == 0
    output = capsys.readouterr().out
    assert "cli-demo: Renamed Demo (custom)" in output
    assert "0: #000000" in output
    assert "1: #FF0000" in output
    assert "2: #000000" in output

    native = store / "cli-demo.retropal-palette.json"
    source = tmp_path / "source.png"
    target = tmp_path / "custom.png"
    Image.new("RGBA", (3, 2), (120, 120, 120, 255)).save(source)
    assert (
        main(
            [
                "convert",
                str(source),
                "--custom-palette",
                str(native),
                "--dither",
                "floyd-steinberg",
                "-o",
                str(target),
            ]
        )
        == 0
    )
    assert target.exists()
    assert {pixel[:3] for pixel in Image.open(target).convert("RGBA").get_flattened_data()} <= {
        (0, 0, 0),
        (255, 0, 0),
    }


def test_custom_palette_cli_reports_invalid_native_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    malformed = tmp_path / "bad.retropal-palette.json"
    malformed.write_text("not json", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        main(["custom-palettes", "--store", str(tmp_path / "store"), "load", str(malformed)])
    assert exc_info.value.code == 2
    assert "Malformed native palette JSON" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("format_id", "suffix"),
    [("gpl", ".gpl"), ("riff-pal", ".pal"), ("json", ".json")],
)
def test_custom_palette_cli_interchange_import_export(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    format_id: str,
    suffix: str,
) -> None:
    source_store = tmp_path / "source-store"
    source_common = ["custom-palettes", "--store", str(source_store)]
    assert (
        main(
            [
                *source_common,
                "create",
                "interchange-demo",
                "Interchange Demo",
                "#010203",
                "#FF0080",
                "#010203",
                "--description",
                "CLI fixture",
            ]
        )
        == 0
    )
    exported = tmp_path / f"exported{suffix}"
    assert (
        main(
            [
                *source_common,
                "export",
                "interchange-demo",
                "--format",
                format_id,
                "--output",
                str(exported),
            ]
        )
        == 0
    )
    assert exported.exists()
    export_output = capsys.readouterr().out
    assert "Interchange report:" in export_output
    if format_id == "json":
        assert "lossless" in export_output
    else:
        assert "Warning:" in export_output

    target_store = tmp_path / "target-store"
    assert (
        main(
            [
                "custom-palettes",
                "--store",
                str(target_store),
                "import",
                str(exported),
                "--format",
                format_id,
            ]
        )
        == 0
    )
    imported_files = tuple(target_store.glob("*.retropal-palette.json"))
    assert len(imported_files) == 1


@pytest.mark.parametrize(
    ("suffix", "data", "format_name"),
    [
        (".png", indexed_png(((0, 0, 0), (255, 0, 0), (0, 0, 0))), "PNG"),
        (".gif", indexed_gif(((0, 0, 0), (255, 0, 0))), "GIF"),
        (".bmp", indexed_bmp(8, ((0, 0, 0), (255, 0, 0)), (1,)), "BMP"),
    ],
)
def test_custom_palette_cli_imports_indexed_images(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    suffix: str,
    data: bytes,
    format_name: str,
) -> None:
    image = tmp_path / f"CLI Image{suffix}"
    image.write_bytes(data)
    store = tmp_path / "store"
    assert (
        main(
            [
                "custom-palettes",
                "--store",
                str(store),
                "import-image",
                str(image),
                "--id",
                f"cli-{format_name.casefold()}",
                "--name",
                f"CLI {format_name}",
            ]
        )
        == 0
    )
    saved = next(store.glob("*.retropal-palette.json"))
    palette = load_native_palette(saved)
    assert palette.colors[0] == (0, 0, 0)
    assert f"stored {format_name} entries" in capsys.readouterr().out
