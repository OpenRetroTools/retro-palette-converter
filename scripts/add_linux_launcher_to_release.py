"""Add the Linux launcher and platform notes to the packaged release ZIP."""

from __future__ import annotations

import argparse
import stat
import tempfile
import zipfile
from pathlib import Path

LAUNCHER_NAME = "RetroPaletteConverter.sh"

LAUNCHER = r"""#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

is_crostini() {
    [[ -n "${CROS_USER_ID_HASH:-}" ]] && return 0
    [[ -e /dev/.cros_milestone ]] && return 0
    [[ -e /mnt/chromeos ]] && return 0

    grep -Eqi \
        'chromeos|cros|termina' \
        /proc/version /etc/os-release 2>/dev/null
}

# Respect an explicit user selection.
if [[ -z "${QT_QPA_PLATFORM:-}" ]] && is_crostini; then
    export QT_QPA_PLATFORM=xcb
fi

exec "$APP_DIR/RetroPaletteConverter" "$@"
"""

NOTES = r"""Retro Palette Converter for Linux
==========================================

Normal Linux
------------

You can start the native binary directly:

    ./RetroPaletteConverter

ChromeOS / Crostini
-------------------

Use the included launcher:

    ./RetroPaletteConverter.sh

The launcher detects Crostini and selects Qt's XCB backend to avoid known
Wayland connection failures. It does not force XCB on ordinary Linux systems.

If the launcher is not executable after extraction:

    chmod +x RetroPaletteConverter.sh

Required Crostini packages when XCB libraries are missing:

    sudo apt update
    sudo apt install -y \
      libxcb-cursor0 \
      libxkbcommon-x11-0 \
      libxcb-xinerama0 \
      libxcb-icccm4 \
      libxcb-image0 \
      libxcb-keysyms1 \
      libxcb-render-util0
"""


def update_zip(archive: Path) -> None:
    if not archive.is_file():
        raise FileNotFoundError(f"Linux release archive not found: {archive}")

    with tempfile.TemporaryDirectory(prefix="retropal-linux-release-") as temp_dir:
        temp = Path(temp_dir)
        unpacked = temp / "unpacked"
        unpacked.mkdir()

        with zipfile.ZipFile(archive, "r") as source:
            source.extractall(unpacked)

        roots = [path for path in unpacked.iterdir()]
        package_root = roots[0] if len(roots) == 1 and roots[0].is_dir() else unpacked

        launcher = package_root / LAUNCHER_NAME
        launcher.write_text(LAUNCHER, encoding="utf-8", newline="\n")
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        notes = package_root / "README-LINUX.txt"
        notes.write_text(NOTES, encoding="utf-8", newline="\n")

        replacement = temp / archive.name
        with zipfile.ZipFile(
            replacement,
            "w",
            compression=zipfile.ZIP_DEFLATED,
        ) as destination:
            for path in sorted(unpacked.rglob("*")):
                if path.is_file():
                    info = zipfile.ZipInfo.from_file(
                        path,
                        arcname=path.relative_to(unpacked),
                    )
                    with path.open("rb") as handle:
                        destination.writestr(
                            info,
                            handle.read(),
                            compress_type=zipfile.ZIP_DEFLATED,
                        )

        replacement.replace(archive)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "archive",
        nargs="?",
        type=Path,
        default=Path("dist/retro-palette-converter-linux-x86_64.zip"),
    )
    args = parser.parse_args()

    update_zip(args.archive)
    print(f"Added Crostini-aware launcher to {args.archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
