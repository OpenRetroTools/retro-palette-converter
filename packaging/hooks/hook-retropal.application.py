"""Collect Qt libraries that are loaded indirectly by Linux platform plugins."""

from __future__ import annotations

import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

binaries = []
datas = collect_data_files(
    "retropal.palettes.definitions",
    includes=["*.json"],
)

if sys.platform.startswith("linux"):
    # Qt's platform plugins are loaded at runtime, so their Qt-private shared
    # library dependencies are not always discovered by PyInstaller's binary
    # analysis. Preserve PySide6's directory layout so the plugins' $ORIGIN
    # relative RUNPATH resolves these libraries without LD_LIBRARY_PATH.
    binaries += collect_dynamic_libs(
        "PySide6",
        search_patterns=["libQt6*Qpa.so*", "libQt6Wayland*.so*"],
    )
