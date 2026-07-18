from __future__ import annotations

import importlib.util
import stat
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "add_linux_launcher_to_release.py"


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
        output.writestr(
            "RetroPaletteConverter/RetroPaletteConverter",
            b"fake executable",
        )

    module.update_zip(archive)

    with zipfile.ZipFile(archive) as result:
        launcher_name = "RetroPaletteConverter/RetroPaletteConverter.sh"
        notes_name = "RetroPaletteConverter/README-LINUX.txt"

        assert launcher_name in result.namelist()
        assert notes_name in result.namelist()

        launcher = result.read(launcher_name).decode()
        assert "QT_QPA_PLATFORM=xcb" in launcher
        assert "CROS_USER_ID_HASH" in launcher
        assert 'exec "$APP_DIR/RetroPaletteConverter"' in launcher

        mode = result.getinfo(launcher_name).external_attr >> 16
        assert mode & stat.S_IXUSR
