"""Add the Linux launcher and platform notes to the packaged release ZIP."""

from __future__ import annotations

import argparse
import copy
import shutil
import stat
import zipfile
from pathlib import Path
from pathlib import PurePosixPath

LAUNCHER_NAME = "RetroPaletteConverter.sh"
EXECUTABLE_NAMES = {"RetroPaletteConverter", "retropal", LAUNCHER_NAME}

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
An explicitly configured QT_QPA_PLATFORM value is always respected.

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
    """Add the launcher and notes, replacing *archive* atomically."""
    archive = archive.resolve()
    if not archive.is_file():
        raise FileNotFoundError(f"Linux release archive not found: {archive}")

    # Repack directly from the original ZipInfo records. Extracting first loses
    # Unix modes because ZipFile.extractall() does not restore permission bits.
    replacement = archive.with_name(f".{archive.name}.tmp")
    try:
        with zipfile.ZipFile(archive, "r") as source:
            entries = source.infolist()
            top_levels = {PurePosixPath(info.filename).parts[0] for info in entries}
            prefix = f"{top_levels.pop()}/" if len(top_levels) == 1 else ""
            added_names = {f"{prefix}{LAUNCHER_NAME}", f"{prefix}README-LINUX.txt"}

            with zipfile.ZipFile(
                replacement,
                "w",
                compression=zipfile.ZIP_DEFLATED,
            ) as destination:
                destination.comment = source.comment
                for original_info in entries:
                    if original_info.filename in added_names:
                        continue
                    info = copy.copy(original_info)
                    if PurePosixPath(info.filename).name in EXECUTABLE_NAMES:
                        info.create_system = 3
                        info.external_attr = (stat.S_IFREG | 0o755) << 16
                    with source.open(original_info) as source_file:
                        with destination.open(
                            info, "w", force_zip64=True
                        ) as output_file:
                            shutil.copyfileobj(source_file, output_file)

                for name, data, mode in (
                    (f"{prefix}{LAUNCHER_NAME}", LAUNCHER.encode(), 0o755),
                    (f"{prefix}README-LINUX.txt", NOTES.encode(), 0o644),
                ):
                    info = zipfile.ZipInfo(name)
                    info.create_system = 3
                    info.external_attr = (stat.S_IFREG | mode) << 16
                    destination.writestr(
                        info,
                        data,
                        compress_type=zipfile.ZIP_DEFLATED,
                    )

        replacement.replace(archive)
    finally:
        replacement.unlink(missing_ok=True)


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
