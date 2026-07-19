#!/usr/bin/env python3
"""Build a native Retro Palette Converter release archive for the current OS."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
WORK = ROOT / "build" / "pyinstaller"
ENTRY = ROOT / "src" / "retropal" / "gui_entry.py"
APP_NAME = "RetroPaletteConverter"


def run(*args: str) -> None:
    print("+", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)


def clean() -> None:
    shutil.rmtree(DIST, ignore_errors=True)
    shutil.rmtree(WORK, ignore_errors=True)
    spec = ROOT / f"{APP_NAME}.spec"
    if spec.exists():
        spec.unlink()
    DIST.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)


def build() -> None:
    # Do not use --collect-all PySide6. PyInstaller's Qt hook follows the
    # imported QtCore/QtGui/QtWidgets modules and includes their required
    # plugins. Collecting all of PySide6 pulls in WebEngine, QML, 3D, SQL,
    # Multimedia, and other unused components.
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--paths",
        str(ROOT / "src"),
        "--distpath",
        str(DIST),
        "--workpath",
        str(WORK),
        "--specpath",
        str(WORK),
        "--additional-hooks-dir",
        str(ROOT / "packaging" / "hooks"),
        "--exclude-module",
        "PySide6.QtWebEngineCore",
        "--exclude-module",
        "PySide6.QtWebEngineWidgets",
        "--exclude-module",
        "PySide6.QtWebEngineQuick",
        "--exclude-module",
        "PySide6.QtQml",
        "--exclude-module",
        "PySide6.QtQuick",
        "--exclude-module",
        "PySide6.QtQuickWidgets",
        "--exclude-module",
        "PySide6.Qt3DCore",
        "--exclude-module",
        "PySide6.Qt3DRender",
        "--exclude-module",
        "PySide6.QtMultimedia",
        "--exclude-module",
        "PySide6.QtSql",
        str(ENTRY),
    ]

    icon_ico = ROOT / "packaging" / "icons" / "retropal.ico"
    icon_icns = ROOT / "packaging" / "icons" / "retropal.icns"
    system = platform.system()

    if system == "Windows" and icon_ico.exists():
        args[args.index(str(ENTRY)) : args.index(str(ENTRY))] = ["--icon", str(icon_ico)]
    elif system == "Darwin" and icon_icns.exists():
        args[args.index(str(ENTRY)) : args.index(str(ENTRY))] = [
            "--icon",
            str(icon_icns),
            "--osx-bundle-identifier",
            "org.openretrotools.retropaletteconverter",
        ]

    run(*args)

    if platform.system() == "Linux":
        run(
            sys.executable,
            str(ROOT / "scripts" / "verify_linux_qt_plugins.py"),
            str(DIST / APP_NAME),
        )
        run(
            sys.executable,
            str(ROOT / "scripts" / "verify_packaged_palettes.py"),
            str(DIST / APP_NAME),
        )


def add_release_files(bundle: Path) -> None:
    for name in ("README.md", "LICENSE", "CHANGELOG.md"):
        source = ROOT / name
        if source.exists():
            shutil.copy2(source, bundle / name)


def add_linux_release_files(bundle: Path) -> None:
    """Add the preferred Linux launcher and platform notes to the bundle."""
    packaging = ROOT / "packaging" / "linux"
    launcher = bundle / "RetroPaletteConverter.sh"
    shutil.copy2(packaging / launcher.name, launcher)
    launcher.chmod(0o755)
    shutil.copy2(packaging / "README-LINUX.txt", bundle / "README-LINUX.txt")


def archive() -> Path:
    system = platform.system()
    machine = platform.machine().lower().replace("amd64", "x86_64")
    if machine in {"arm64", "aarch64"}:
        machine = "arm64"

    if system == "Windows":
        bundle = DIST / APP_NAME
        add_release_files(bundle)
        archive_path = DIST / f"retro-palette-converter-windows-{machine}.zip"
        make_zip_atomically(archive_path, APP_NAME)
    elif system == "Darwin":
        app = DIST / f"{APP_NAME}.app"
        if not app.exists():
            raise FileNotFoundError(f"Expected macOS app bundle: {app}")
        extras = DIST / "release-files"
        extras.mkdir(exist_ok=True)
        add_release_files(extras)
        archive_path = DIST / f"retro-palette-converter-macos-{machine}.zip"
        archive_path.unlink(missing_ok=True)
        with tempfile.TemporaryDirectory(prefix=".archive-", dir=DIST) as temp_dir:
            temporary_archive = Path(temp_dir) / archive_path.name
            # ditto preserves bundle metadata and symlinks correctly.
            run(
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(app),
                str(temporary_archive),
            )
            temporary_archive.replace(archive_path)
    elif system == "Linux":
        bundle = DIST / APP_NAME
        add_release_files(bundle)
        add_linux_release_files(bundle)
        archive_path = DIST / f"retro-palette-converter-linux-{machine}.zip"
        make_zip_atomically(archive_path, APP_NAME)
    else:
        raise RuntimeError(f"Unsupported build platform: {system}")

    print(f"Created {archive_path}")
    return archive_path


def make_zip_atomically(archive_path: Path, bundle_name: str) -> None:
    """Create a ZIP without exposing an incomplete artifact at its final path."""
    archive_path.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix=".archive-", dir=DIST) as temp_dir:
        temporary_base = Path(temp_dir) / archive_path.stem
        temporary_archive = Path(shutil.make_archive(str(temporary_base), "zip", DIST, bundle_name))
        temporary_archive.replace(archive_path)


def main() -> int:
    clean()
    build()
    archive()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
