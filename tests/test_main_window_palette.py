from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication

from retropal.gui.main_window import MainWindow
from retropal.palettes import palette_colors
from retropal.palettes.fixed import load_fixed_palette


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture
def window(qt_app: QApplication, tmp_path: Path) -> MainWindow:
    source = tmp_path / "source.png"
    image = Image.new("RGB", (4, 1))
    image.putdata([(8, 16, 24), (192, 64, 32), (48, 160, 80), (224, 208, 176)])
    image.save(source)
    main_window = MainWindow()
    main_window.load_path(source)
    qt_app.processEvents()
    return main_window


def select_palette(
    window: MainWindow,
    qt_app: QApplication,
    palette_id: str,
) -> tuple[tuple[int, int, int], ...]:
    window._palette_combo.setCurrentText(palette_id)
    qt_app.processEvents()
    assert window._controller.palette_id == palette_id
    return window._palette_view.colors


@pytest.mark.parametrize("palette_id", ["commodore-64", "atari-st"])
def test_selecting_fixed_palette_displays_registered_colors(
    window: MainWindow,
    qt_app: QApplication,
    palette_id: str,
) -> None:
    displayed = select_palette(window, qt_app, palette_id)

    assert displayed == load_fixed_palette(palette_id).colors
    assert window._controller.converted_image is not None
    converted_colors = {
        pixel[:3]
        for pixel in window._controller.converted_image.convert("RGBA").get_flattened_data()
        if pixel[3] > 0
    }
    assert converted_colors <= set(displayed)


def test_selecting_adaptive_amiga_palette_displays_generated_colors(
    window: MainWindow,
    qt_app: QApplication,
) -> None:
    displayed = select_palette(window, qt_app, "amiga-ocs-16")
    source_image = window._controller.source_image
    assert source_image is not None

    assert displayed == palette_colors("amiga-ocs-16", source_image)


def test_switching_from_amiga_to_atari_refreshes_swatches(
    window: MainWindow,
    qt_app: QApplication,
) -> None:
    amiga = select_palette(window, qt_app, "amiga-ocs-16")
    atari = select_palette(window, qt_app, "atari-st")

    assert atari == load_fixed_palette("atari-st").colors
    assert atari != amiga


def test_switching_between_fixed_palettes_refreshes_swatches(
    window: MainWindow,
    qt_app: QApplication,
) -> None:
    commodore = select_palette(window, qt_app, "commodore-64")
    atari = select_palette(window, qt_app, "atari-2600-tia")

    assert commodore == load_fixed_palette("commodore-64").colors
    assert atari == load_fixed_palette("atari-2600-tia").colors
    assert atari != commodore


def test_dither_change_preserves_displayed_palette(
    window: MainWindow,
    qt_app: QApplication,
) -> None:
    colors = select_palette(window, qt_app, "commodore-64")
    window._dither_combo.setCurrentIndex(1)
    qt_app.processEvents()

    assert window._palette_view.colors == colors


def test_window_without_image_keeps_empty_palette(qt_app: QApplication) -> None:
    window = MainWindow()
    window.refresh_conversion()
    qt_app.processEvents()

    assert window._palette_view.colors == ()
    assert window._palette_metadata.text() == "No palette generated"
