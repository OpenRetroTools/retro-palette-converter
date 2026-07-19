from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "add_linux_launcher_to_release.py"
LAUNCHER = Path(__file__).parents[1] / "packaging" / "linux" / "RetroPaletteConverter.sh"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "add_linux_launcher_to_release",
        SCRIPT,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_adds_crostini_launcher_to_linux_zip(tmp_path: Path) -> None:
    module = load_module()
    archive = tmp_path / "retro-palette-converter-linux-x86_64.zip"

    with zipfile.ZipFile(archive, "w") as output:
        for executable in ("RetroPaletteConverter", "retropal"):
            info = zipfile.ZipInfo(f"RetroPaletteConverter/{executable}")
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o755) << 16
            output.writestr(info, b"fake executable")

    module.update_zip(archive)

    with zipfile.ZipFile(archive) as result:
        launcher_name = "RetroPaletteConverter/RetroPaletteConverter.sh"
        notes_name = "RetroPaletteConverter/README-LINUX.txt"

        assert launcher_name in result.namelist()
        assert notes_name in result.namelist()

        launcher = result.read(launcher_name).decode()
        assert "QT_QPA_PLATFORM=xcb" in launcher
        assert "SOMMELIER_VERSION" in launcher
        assert 'exec "$APP_DIR/RetroPaletteConverter"' in launcher

        executable_names = (
            "RetroPaletteConverter/RetroPaletteConverter",
            "RetroPaletteConverter/retropal",
            launcher_name,
        )
        for name in executable_names:
            mode = result.getinfo(name).external_attr >> 16
            assert stat.S_IMODE(mode) == 0o755


def test_replacement_archive_is_created_beside_destination() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'archive.with_name(f".{archive.name}.tmp")' in source
    assert "Path(temp_dir) / archive.name" not in source


def run_launcher(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    environment: dict[str, str] | None = None,
    arguments: tuple[str, ...] = (),
    exit_status: int = 0,
) -> subprocess.CompletedProcess[str]:
    launcher = tmp_path / LAUNCHER.name
    launcher.write_bytes(LAUNCHER.read_bytes())
    launcher.chmod(0o755)

    executable = tmp_path / "RetroPaletteConverter"
    executable.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "${QT_QPA_PLATFORM-<unset>}"\n'
        'printf "arg=%s\\n" "$@"\n'
        f"exit {exit_status}\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)

    for name in (
        "SOMMELIER_VERSION",
        "CROS_USER_ID_HASH",
        "CHROMEOS_RELEASE_NAME",
        "QT_QPA_PLATFORM",
    ):
        monkeypatch.delenv(name, raising=False)

    launch_environment = os.environ.copy()
    launch_environment.update(environment or {})
    return subprocess.run(
        [str(launcher), *arguments],
        check=False,
        capture_output=True,
        text=True,
        env=launch_environment,
    )


def test_crostini_defaults_to_xcb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_launcher(
        tmp_path,
        monkeypatch,
        environment={"SOMMELIER_VERSION": "1.2.3"},
    )

    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "xcb"


def test_explicit_qt_platform_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    result = run_launcher(
        tmp_path,
        monkeypatch,
        environment={"SOMMELIER_VERSION": "1.2.3", "QT_QPA_PLATFORM": "wayland"},
    )

    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "wayland"


def test_normal_linux_does_not_force_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = run_launcher(tmp_path, monkeypatch)

    assert result.returncode == 0
    assert result.stdout.splitlines()[0] == "<unset>"


def test_arguments_and_exit_status_are_forwarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = run_launcher(
        tmp_path,
        monkeypatch,
        arguments=("input file.png", "--palette", "gameboy"),
        exit_status=37,
    )

    assert result.returncode == 37
    assert result.stdout.splitlines()[1:] == [
        "arg=input file.png",
        "arg=--palette",
        "arg=gameboy",
    ]
