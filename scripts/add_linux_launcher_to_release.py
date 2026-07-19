"""Add the Linux launcher and platform notes to the packaged release ZIP."""

from __future__ import annotations

import argparse
import copy
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
LINUX_PACKAGING = ROOT / "packaging" / "linux"
LAUNCHER_NAME = "RetroPaletteConverter.sh"
EXECUTABLE_NAMES = {"RetroPaletteConverter", "retropal", LAUNCHER_NAME}


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
                    with (
                        source.open(original_info) as source_file,
                        destination.open(info, "w", force_zip64=True) as output_file,
                    ):
                        shutil.copyfileobj(source_file, output_file)

                for name, data, mode in (
                    (
                        f"{prefix}{LAUNCHER_NAME}",
                        (LINUX_PACKAGING / LAUNCHER_NAME).read_bytes(),
                        0o755,
                    ),
                    (
                        f"{prefix}README-LINUX.txt",
                        (LINUX_PACKAGING / "README-LINUX.txt").read_bytes(),
                        0o644,
                    ),
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
