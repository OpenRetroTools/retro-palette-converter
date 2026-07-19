from __future__ import annotations

import os
from hashlib import sha256
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication

from retropal.core.converter import convert
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
    colors = (
        (8, 16, 24),
        (192, 64, 32),
        (48, 160, 80),
        (224, 208, 176),
        (40, 96, 208),
        (240, 32, 160),
        (32, 224, 224),
        (0, 0, 250),
    )
    image = Image.new("RGB", (64, 64))
    image.putdata(
        [colors[(x // 16 + y // 16 * 4) % len(colors)] for y in range(64) for x in range(64)]
    )
    image.save(source)
    main_window = MainWindow()
    main_window.show()
    main_window.load_path(source)
    qt_app.processEvents()
    return main_window


def select_palette(
    window: MainWindow,
    qt_app: QApplication,
    palette_id: str,
) -> tuple[tuple[int, int, int], ...]:
    window._palette_combo.setCurrentIndex(window._palette_combo.findData(palette_id))
    qt_app.processEvents()
    assert window._controller.palette_id == palette_id
    return window._palette_view.colors


@pytest.mark.parametrize("palette_id", ["amiga-ocs-16", "commodore-64", "atari-st"])
def test_palette_signal_updates_controller_conversion_and_panel(
    window: MainWindow,
    qt_app: QApplication,
    palette_id: str,
) -> None:
    index_spy = QSignalSpy(window._palette_combo.currentIndexChanged)
    index = window._palette_combo.findData(palette_id)
    assert index >= 0
    assert window._palette_combo.itemData(index) == palette_id

    window._palette_combo.setCurrentIndex(index)
    qt_app.processEvents()

    assert index_spy.count() == 1
    assert window._palette_combo.currentData() == palette_id
    assert window._controller.palette_id == palette_id
    source_image = window._controller.source_image
    converted_image = window._controller.converted_image
    assert source_image is not None
    assert converted_image is not None
    expected_image = convert(source_image, palette_id, window._controller.dither)
    assert converted_image.tobytes() == expected_image.tobytes()
    assert window._palette_view.colors == palette_colors(palette_id, source_image)


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


def qimage_checksum(window: MainWindow) -> str:
    image = window._converted_view.pixmap().toImage().convertToFormat(QImage.Format.Format_RGBA8888)
    return sha256(bytes(image.constBits())[: image.sizeInBytes()]).hexdigest()


def visible_swatch_colors(window: MainWindow) -> tuple[tuple[int, int, int], ...]:
    colors = []
    for index in range(window._palette_view.swatch_count):
        swatch = window._palette_view._layout.itemAt(index).widget()
        assert swatch is not None
        image = swatch.grab().toImage()
        color = image.pixelColor(image.width() // 2, image.height() // 2)
        colors.append((color.red(), color.green(), color.blue()))
    return tuple(colors)


def choose_palette_like_user(
    window: MainWindow,
    qt_app: QApplication,
    palette_id: str,
) -> None:
    combo = window._palette_combo
    index = combo.findData(palette_id)
    assert index >= 0
    combo.showPopup()
    qt_app.processEvents()
    model_index = combo.model().index(index, combo.modelColumn(), combo.rootModelIndex())
    combo.view().scrollTo(model_index)
    target = combo.view().visualRect(model_index).center()
    QTest.mouseClick(combo.view().viewport(), Qt.MouseButton.LeftButton, pos=target)
    qt_app.processEvents()


def test_visible_palette_sequence_updates_pixmap_and_swatch_widgets(
    window: MainWindow,
    qt_app: QApplication,
    tmp_path: Path,
) -> None:
    sequence = (
        "amiga-ocs-16",
        "commodore-64",
        "atari-st",
        "amiga-ocs-16",
        "commodore-64",
    )
    results: list[tuple[str, tuple[tuple[int, int, int], ...]]] = []

    for step, palette_id in enumerate(sequence, start=1):
        choose_palette_like_user(window, qt_app, palette_id)
        assert window._palette_combo.currentData() == palette_id
        expected_name = (
            "Amiga OCS 16"
            if palette_id.startswith("amiga-")
            else load_fixed_palette(palette_id).name
        )
        assert window._palette_combo.currentText() == expected_name
        visible_colors = visible_swatch_colors(window)
        expected_colors = tuple(window._palette_view.colors)
        assert visible_colors == expected_colors
        assert window._palette_view.swatch_count == len(expected_colors)
        assert window._converted_view.pixmap().cacheKey() != 0
        screenshot_dir = Path(os.environ.get("RETROPAL_PALETTE_SCREENSHOT_DIR", tmp_path))
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        assert window.grab().save(str(screenshot_dir / f"palette-step-{step}-{palette_id}.png"))
        results.append((qimage_checksum(window), visible_colors))

    amiga_first, commodore_first, atari, amiga_second, commodore_second = results
    assert commodore_first[1] == load_fixed_palette("commodore-64").colors
    assert atari[1] == load_fixed_palette("atari-st").colors
    assert commodore_first[0] != amiga_first[0]
    assert atari[0] != amiga_first[0]
    assert amiga_second == amiga_first
    assert commodore_second == commodore_first


def test_sinclair_profile_selection_updates_visible_palette(
    window: MainWindow,
    qt_app: QApplication,
) -> None:
    profile_index = window._profile_combo.findData("sinclair-zx-spectrum-48k")
    assert profile_index >= 0
    window._profile_combo.setCurrentIndex(profile_index)
    qt_app.processEvents()

    assert window._profile_combo.currentText() == "Sinclair ZX Spectrum 48K"
    assert window._palette_combo.currentData() == "zx-spectrum-48k-auto"
    assert window._palette_combo.count() == 3
    assert visible_swatch_colors(window) == load_fixed_palette("zx-spectrum-48k-auto").colors

    auto_checksum = qimage_checksum(window)
    choose_palette_like_user(window, qt_app, "zx-spectrum-48k-normal")
    assert visible_swatch_colors(window) == load_fixed_palette("zx-spectrum-48k-normal").colors
    assert qimage_checksum(window) != auto_checksum
