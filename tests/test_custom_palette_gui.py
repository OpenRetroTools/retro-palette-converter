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
from tests.ilbm_fixtures import rich_ilbm
from tests.indexed_image_fixtures import indexed_png


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


def test_custom_palette_dialog_uses_registry_for_interchange_filters(
    qt_app: QApplication,
    tmp_path: Path,
) -> None:
    dialog = CustomPaletteDialog(CustomPaletteStore(tmp_path))
    filters, mapping = dialog._codec_filters()

    assert "GIMP GPL (*.gpl)" in filters
    assert "JASC-PAL (*.pal)" in filters
    assert "Microsoft RIFF PAL (*.pal)" in filters
    assert "Brilliance palette (verified ILBM variant) (*.plt)" in filters
    assert set(mapping.values()) == {
        "gpl",
        "jasc",
        "riff-pal",
        "act",
        "json",
        "csv",
        "brilliance-plt",
    }
    export_filters, export_mapping = dialog._codec_filters(for_export=True)
    assert "Brilliance" not in export_filters
    assert "brilliance-plt" not in export_mapping.values()


def test_custom_palette_dialog_exports_and_imports_through_shared_codecs(
    qt_app: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    source_store = CustomPaletteStore(tmp_path / "source")
    colors = ((1, 2, 3), (255, 0, 128), (1, 2, 3))
    source_store.create("gui-interchange", "GUI Interchange", colors)
    source_dialog = CustomPaletteDialog(source_store)
    output = tmp_path / "gui-export.gpl"
    selected_filter = "GIMP GPL (*.gpl)"
    messages: list[str] = []
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output), selected_filter),
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: messages.append(message),
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    source_dialog._export_palette()

    assert output.exists()
    assert messages and "stable palette ID" in messages[0]

    target_store = CustomPaletteStore(tmp_path / "target")
    target_dialog = CustomPaletteDialog(target_store)
    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(output), selected_filter),
    )
    target_dialog._import_palette()

    assert target_store.list()[0].colors == colors


def test_custom_palette_dialog_validation_uses_shared_plan(
    qt_app: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PySide6.QtWidgets import QInputDialog, QMessageBox

    store = CustomPaletteStore(tmp_path)
    store.create("gui-validation", "GUI Validation", ((18, 52, 86),))
    dialog = CustomPaletteDialog(store)
    reports: list[str] = []
    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        lambda *args, **kwargs: ("hardware:amiga-ocs-16", True),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: reports.append(message),
    )

    dialog._validate_palette()

    assert reports and "Exactness: rgb-loss" in reports[0]
    assert "channel-precision-loss" in reports[0]


def test_custom_palette_dialog_imports_indexed_image_with_report(
    qt_app: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    image = tmp_path / "gui-indexed.png"
    colors = ((0, 0, 0), (255, 0, 0), (0, 0, 0))
    image.write_bytes(indexed_png(colors, transparency=b"\x00"))
    store = CustomPaletteStore(tmp_path / "store")
    dialog = CustomPaletteDialog(store)
    reports: list[str] = []
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(image), ""))
    monkeypatch.setattr(
        QMessageBox, "warning", lambda _parent, _title, message: reports.append(message)
    )

    dialog._import_indexed_image()

    assert store.list()[0].colors == colors
    assert store.path_for("gui-indexed").exists()
    assert reports and "all 3 stored entries" in reports[0]
    assert "Non-opaque indexes: 0" in reports[0]


def test_custom_palette_dialog_imports_and_updates_ilbm(
    qt_app: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    source = tmp_path / "amiga.iff"
    output = tmp_path / "updated.iff"
    source.write_bytes(rich_ilbm())
    store = CustomPaletteStore(tmp_path / "store")
    dialog = CustomPaletteDialog(store)
    warnings: list[str] = []
    information: list[str] = []
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(source), ""))
    monkeypatch.setattr(
        QMessageBox, "warning", lambda _parent, _title, message: warnings.append(message)
    )
    monkeypatch.setattr(
        QMessageBox, "information", lambda _parent, _title, message: information.append(message)
    )

    dialog._import_ilbm()

    assert store.list()[0].colors == ((1, 2, 3), (255, 0, 128), (1, 2, 3))
    assert warnings and "CRNG 1: indexes 4–7, rate 8192" in warnings[0]

    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(output), ""))
    dialog._update_ilbm()

    assert output.exists()
    assert information and "all other chunk payloads" in information[-1]
