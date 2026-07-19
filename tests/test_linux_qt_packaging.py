from __future__ import annotations

import importlib.util
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
VERIFY_SCRIPT = ROOT / "scripts" / "verify_linux_qt_plugins.py"
VERIFY_PALETTES_SCRIPT = ROOT / "scripts" / "verify_packaged_palettes.py"
BUILD_SCRIPT = ROOT / "scripts" / "build_release.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_plugin_tree(tmp_path: Path) -> tuple[object, Path, Path]:
    module = load_module(VERIFY_SCRIPT, "verify_linux_qt_plugins")
    bundle = tmp_path / "RetroPaletteConverter"
    plugin = bundle / module.PLATFORM_PLUGIN_DIR / "libqxcb.so"
    plugin.parent.mkdir(parents=True)
    plugin.touch()
    return module, bundle, plugin


def test_xcb_plugin_requires_private_qt_library(tmp_path: Path) -> None:
    module, bundle, _plugin = make_plugin_tree(tmp_path)

    with pytest.raises(RuntimeError, match="libQt6XcbQpa.so.6 is missing"):
        module.verify_bundle(bundle)


def test_xcb_plugin_rejects_unresolved_ldd_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module, bundle, _plugin = make_plugin_tree(tmp_path)
    qt_library = bundle / module.QT_LIBRARY_DIR / "libQt6XcbQpa.so.6"
    qt_library.parent.mkdir(parents=True)
    qt_library.touch()
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, "libQt6XcbQpa.so.6 => not found\n", ""
        ),
    )

    with pytest.raises(RuntimeError, match="libQt6XcbQpa.so.6 => not found"):
        module.verify_bundle(bundle)


def test_failed_zip_creation_leaves_no_final_archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_module(BUILD_SCRIPT, "build_release")
    monkeypatch.setattr(module, "DIST", tmp_path)
    archive = tmp_path / "release.zip"
    archive.write_bytes(b"stale archive")

    def fail_archive(base: str, *args, **kwargs):
        Path(f"{base}.zip").write_bytes(b"partial archive")
        raise OSError("disk full")

    monkeypatch.setattr(module.shutil, "make_archive", fail_archive)

    with pytest.raises(OSError, match="disk full"):
        module.make_zip_atomically(archive, "RetroPaletteConverter")

    assert not archive.exists()


def test_linux_bundle_includes_preferred_launcher(tmp_path: Path) -> None:
    module = load_module(BUILD_SCRIPT, "build_release_with_launcher")
    bundle = tmp_path / "RetroPaletteConverter"
    bundle.mkdir()

    module.add_linux_release_files(bundle)

    launcher = bundle / "RetroPaletteConverter.sh"
    assert launcher.is_file()
    assert stat.S_IMODE(launcher.stat().st_mode) == 0o755
    assert (bundle / "README-LINUX.txt").is_file()
    assert "SOMMELIER_VERSION" in launcher.read_text(encoding="utf-8")


def test_packaged_fixed_palette_definitions_are_required(tmp_path: Path) -> None:
    module = load_module(VERIFY_PALETTES_SCRIPT, "verify_packaged_palettes")
    bundle = tmp_path / "RetroPaletteConverter"

    with pytest.raises(RuntimeError, match="commodore-64,.*atari-st"):
        module.verify_bundle(bundle)


def test_packaged_fixed_palette_definitions_are_accepted(tmp_path: Path) -> None:
    module = load_module(VERIFY_PALETTES_SCRIPT, "verify_packaged_palettes_complete")
    bundle = tmp_path / "RetroPaletteConverter"
    definitions = bundle / "_internal/retropal/palettes/definitions"
    definitions.mkdir(parents=True)
    for palette_id in module.fixed_palette_ids():
        (definitions / f"{palette_id}.json").write_text("{}", encoding="utf-8")

    module.verify_bundle(bundle)

    assert (definitions / "zx-spectrum-48k-auto.json").is_file()
    assert (definitions / "zx-spectrum-128k-bright.json").is_file()
