from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox

from retropal.gui.amiga_cycle_dialog import AmigaCycleDialog
from retropal.palettes.amiga_iff import parse_ilbm
from tests.test_amiga_cycling import indexed_fixture


@pytest.fixture(scope="module")
def qt_app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_cycle_dialog_load_edit_preview_controls_and_safe_save(
    qt_app: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.iff"
    output = tmp_path / "saved.iff"
    source.write_bytes(indexed_fixture())
    dialog = AmigaCycleDialog(source)

    assert dialog._ranges.count() == 1
    assert dialog._swatches.count() == 4
    assert dialog._image.pixmap() is not None
    dialog._rate.setValue(8192)
    dialog._direction.setCurrentIndex(1)
    dialog._apply_range()
    assert dialog.document.color_cycles[0].rate == 8192
    assert dialog.document.color_cycles[0].reversed

    dialog.play()
    assert dialog._playing
    dialog.pause()
    assert not dialog._playing
    dialog.restart()
    assert dialog._elapsed == 0

    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(output), ""))
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    dialog._save_as()

    assert output.exists()
    before = parse_ilbm(source.read_bytes())
    after = parse_ilbm(output.read_bytes())
    assert before.chunks[-1] == after.chunks[-1]
    assert after.color_cycles[0].rate == 8192
    dialog.close()


def test_cycle_dialog_keeps_palette_tools_when_preview_is_unsupported(
    qt_app: QApplication,
    tmp_path: Path,
) -> None:
    source = tmp_path / "metadata-only.iff"
    source.write_bytes(indexed_fixture(camg=0x0800))
    dialog = AmigaCycleDialog(source)

    assert dialog._ranges.count() == 1
    assert "HAM image preview is unsupported" in dialog._status.text()
    dialog.close()
