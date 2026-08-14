from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from retropal.gui.custom_palette_dialog import CustomPaletteDialog
from retropal.gui.main_window import MainWindow
from retropal.palettes.store import CustomPaletteStore


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_custom_palette_dialog_lists_ordered_palette(
    qt_app: QApplication,
    tmp_path: Path,
) -> None:
    store = CustomPaletteStore(tmp_path)
    store.create("gui-demo", "GUI Demo", ((1, 2, 3), (1, 2, 3), (4, 5, 6)))
    dialog = CustomPaletteDialog(store)

    assert dialog._palettes.count() == 1
    assert dialog._colors.count() == 3
    assert dialog._colors.item(0).text().endswith("#010203")
    assert dialog._colors.item(1).text().endswith("#010203")


def test_main_window_selects_custom_palette_for_conversion(
    qt_app: QApplication,
    tmp_path: Path,
) -> None:
    store = CustomPaletteStore(tmp_path / "palettes")
    colors = ((0, 0, 0), (255, 255, 255), (0, 0, 0))
    store.create("gui-conversion", "GUI Conversion", colors)
    source = tmp_path / "source.png"
    Image.new("RGBA", (4, 3), (140, 140, 140, 128)).save(source)
    window = MainWindow(store)
    window.load_path(source)
    index = window._palette_combo.findData("gui-conversion")

    assert index >= 0
    assert window._palette_combo.itemText(index) == "GUI Conversion (Custom)"
    window._palette_combo.setCurrentIndex(index)
    qt_app.processEvents()

    assert window._controller.palette_id == "gui-conversion"
    assert window._controller.display_palette == colors
    assert window._palette_view.colors == colors
    assert "Custom palette" in window._palette_metadata.text()
    assert window._controller.converted_image is not None
    assert {pixel[:3] for pixel in window._controller.converted_image.get_flattened_data()} <= set(
        colors
    )
