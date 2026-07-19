#!/usr/bin/env python3
"""Verify shared-library dependencies of packaged Linux Qt platform plugins."""

from __future__ import annotations

import argparse
import platform
import subprocess
from pathlib import Path

PLATFORM_PLUGIN_DIR = Path("_internal/PySide6/Qt/plugins/platforms")
QT_LIBRARY_DIR = Path("_internal/PySide6/Qt/lib")


def unresolved_dependencies(plugin: Path) -> list[str]:
    """Return unresolved lines from ldd output for *plugin*."""
    result = subprocess.run(
        ["ldd", str(plugin)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"ldd failed for {plugin}: {detail}")
    return [line.strip() for line in result.stdout.splitlines() if "not found" in line]


def verify_plugin(bundle: Path, filename: str, required_qt_library: str) -> None:
    """Verify a packaged plugin and one of its private Qt dependencies."""
    plugin = bundle / PLATFORM_PLUGIN_DIR / filename
    if not plugin.exists():
        return

    required = bundle / QT_LIBRARY_DIR / required_qt_library
    if not required.exists():
        raise RuntimeError(
            f"{filename} is packaged but {required_qt_library} is missing: {required}"
        )

    unresolved = unresolved_dependencies(plugin)
    if unresolved:
        formatted = "\n  ".join(unresolved)
        raise RuntimeError(f"Unresolved dependencies for {plugin}:\n  {formatted}")


def verify_bundle(bundle: Path) -> None:
    """Verify supported Linux Qt platform plugins in *bundle*."""
    verify_plugin(bundle, "libqxcb.so", "libQt6XcbQpa.so.6")
    verify_plugin(bundle, "libqwayland.so", "libQt6WaylandClient.so.6")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bundle",
        nargs="?",
        type=Path,
        default=Path("dist/RetroPaletteConverter"),
    )
    args = parser.parse_args()

    if platform.system() != "Linux":
        print("Skipping Linux Qt plugin verification on this platform")
        return 0

    verify_bundle(args.bundle)
    print(f"Verified packaged Qt platform plugins in {args.bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
