"""Instance-scoped custom palette lifecycle and filesystem storage."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from retropal.palettes import PALETTE_IDS
from retropal.palettes.base import RGBColor
from retropal.palettes.custom import CustomPalette, CustomPaletteError
from retropal.palettes.native import NATIVE_SUFFIX, load_native_palette, save_native_palette


def default_custom_palette_directory() -> Path:
    """Return the per-user native palette directory without requiring Qt."""
    if configured := os.environ.get("RETROPAL_PALETTE_DIR"):
        return Path(configured).expanduser()
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return root / "OpenRetroTools" / "RetroPaletteConverter" / "palettes"
    if sys.platform == "darwin":
        return (
            Path.home() / "Library" / "Application Support" / "RetroPaletteConverter" / "palettes"
        )
    root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "retropal" / "palettes"


class CustomPaletteStore:
    """Manage custom palettes independently of the built-in registry."""

    def __init__(self, directory: Path, *, reserved_ids: tuple[str, ...] = PALETTE_IDS) -> None:
        self.directory = directory
        self._reserved_ids = frozenset(reserved_ids)
        self._palettes: dict[str, CustomPalette] = {}

    @classmethod
    def default(cls) -> CustomPaletteStore:
        return cls(default_custom_palette_directory())

    def create(
        self,
        palette_id: str,
        name: str,
        colors: tuple[RGBColor, ...],
        *,
        description: str = "",
        source: str | None = None,
    ) -> CustomPalette:
        return self.add(CustomPalette(palette_id, name, colors, description, source))

    def add(self, palette: CustomPalette) -> CustomPalette:
        if palette.id in self._reserved_ids:
            raise CustomPaletteError(f"Palette ID is reserved by a built-in palette: {palette.id}")
        if palette.id in self._palettes:
            raise CustomPaletteError(f"Duplicate custom palette ID: {palette.id}")
        self._palettes[palette.id] = palette
        return palette

    def replace(self, palette: CustomPalette) -> CustomPalette:
        if palette.id not in self._palettes:
            raise CustomPaletteError(f"Unknown custom palette: {palette.id}")
        self._palettes[palette.id] = palette
        return palette

    def get(self, palette_id: str) -> CustomPalette:
        try:
            return self._palettes[palette_id]
        except KeyError as exc:
            raise CustomPaletteError(f"Unknown custom palette: {palette_id}") from exc

    def list(self) -> tuple[CustomPalette, ...]:
        return tuple(sorted(self._palettes.values(), key=lambda palette: palette.id))

    def path_for(self, palette_id: str) -> Path:
        return self.directory / f"{palette_id}{NATIVE_SUFFIX}"

    def save(self, palette_id: str, path: Path | None = None) -> Path:
        palette = self.get(palette_id)
        return save_native_palette(palette, path or self.path_for(palette_id))

    def load(self, path: Path) -> CustomPalette:
        return self.add(load_native_palette(path))

    def load_all(self) -> tuple[CustomPalette, ...]:
        if not self.directory.exists():
            self._palettes.clear()
            return ()
        if not self.directory.is_dir():
            raise NotADirectoryError(f"Custom palette store is not a directory: {self.directory}")
        loaded = CustomPaletteStore(self.directory, reserved_ids=tuple(self._reserved_ids))
        for path in sorted(self.directory.glob(f"*{NATIVE_SUFFIX}")):
            loaded.load(path)
        self._palettes = loaded._palettes
        return self.list()

    def delete(self, palette_id: str, *, remove_file: bool = True) -> None:
        self.get(palette_id)
        if remove_file:
            path = self.path_for(palette_id)
            if path.exists():
                path.unlink()
        del self._palettes[palette_id]
