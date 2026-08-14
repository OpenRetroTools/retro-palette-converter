"""Focused Qt editor and deterministic preview for ILBM CRNG ranges."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from retropal.palettes.amiga_iff import (
    ColorCycleRange,
    IlbmPaletteError,
    decode_indexed_ilbm,
    inspect_ilbm,
    palette_at,
    render_indexed_preview,
    validate_cycles,
)
from retropal.palettes.amiga_iff.service import write_cycle_document


class AmigaCycleDialog(QDialog):
    """Edit stored CRNG state while preview controls remain transient."""

    def __init__(self, source: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.source = source
        self.document = inspect_ilbm(source)
        if self.document.palette is None:
            raise IlbmPaletteError("ILBM contains no CMAP palette")
        self._indexed = None
        self._preview_error: str | None = None
        try:
            self._indexed = decode_indexed_ilbm(self.document)
        except IlbmPaletteError as exc:
            self._preview_error = str(exc)
        self._playing = False
        self._origin = 0.0
        self._elapsed = 0.0
        self.setWindowTitle(f"Amiga Colour Cycling — {source.name}")
        self.resize(760, 560)
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._refresh_preview)
        self._refresh_ranges()
        self._refresh_preview()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        self._status = QLabel()
        root.addWidget(self._status)
        body = QHBoxLayout()
        self._ranges = QListWidget()
        self._ranges.currentRowChanged.connect(self._load_range)
        body.addWidget(self._ranges)
        form = QFormLayout()
        self._active = QCheckBox()
        self._direction = QComboBox()
        self._direction.addItems(("Forward", "Reverse"))
        self._rate = QSpinBox()
        self._rate.setRange(0, 65535)
        self._low = QSpinBox()
        self._low.setRange(0, 255)
        self._high = QSpinBox()
        self._high.setRange(0, 255)
        form.addRow("Active", self._active)
        form.addRow("Direction", self._direction)
        form.addRow("Rate", self._rate)
        form.addRow("Low index", self._low)
        form.addRow("High index", self._high)
        body.addLayout(form)
        root.addLayout(body)
        edits = QHBoxLayout()
        for label, callback in (
            ("Add", self._add_range),
            ("Apply", self._apply_range),
            ("Remove", self._remove_range),
            ("Save As…", self._save_as),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            edits.addWidget(button)
        root.addLayout(edits)
        self._swatches = QListWidget()
        self._swatches.setFlow(QListWidget.Flow.LeftToRight)
        root.addWidget(self._swatches)
        self._image = QLabel("No indexed image preview")
        self._image.setMinimumHeight(180)
        root.addWidget(self._image)
        playback = QHBoxLayout()
        for label, callback in (
            ("Play", self.play),
            ("Pause", self.pause),
            ("Restart", self.restart),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            playback.addWidget(button)
        self._speed = QDoubleSpinBox()
        self._speed.setRange(0.1, 8.0)
        self._speed.setValue(1.0)
        self._speed.setSuffix("× preview")
        playback.addWidget(self._speed)
        root.addLayout(playback)

    def _refresh_ranges(self, selected: int = 0) -> None:
        self._ranges.clear()
        for index, cycle in enumerate(self.document.color_cycles):
            state = "active" if cycle.enabled else "inactive"
            direction = "reverse" if cycle.reversed else "forward"
            self._ranges.addItem(
                f"{index}: {cycle.low}–{cycle.high}, rate {cycle.rate}, {state}, {direction}"
            )
        if self._ranges.count():
            self._ranges.setCurrentRow(min(selected, self._ranges.count() - 1))
        self._update_status()

    def _update_status(self) -> None:
        palette = self.document.palette
        assert palette is not None
        issues = validate_cycles(self.document.color_cycles, len(palette.colors))
        unsupported = [
            chunk.id.decode("ascii", "replace")
            for chunk in self.document.chunks
            if chunk.id in {b"DRNG", b"BRNG"}
        ]
        messages = [f"[{issue.code.value}] {issue.message}" for issue in issues]
        if unsupported:
            messages.append("Preserved but not simulated: " + ", ".join(unsupported))
        if self._preview_error:
            messages.append("Image preview unavailable: " + self._preview_error)
        self._status.setText("\n".join(messages) or "CRNG ranges valid")

    def _load_range(self, index: int) -> None:
        if not 0 <= index < len(self.document.color_cycles):
            return
        cycle = self.document.color_cycles[index]
        self._active.setChecked(cycle.enabled)
        self._direction.setCurrentIndex(1 if cycle.reversed else 0)
        self._rate.setValue(cycle.rate)
        self._low.setValue(cycle.low)
        self._high.setValue(cycle.high)

    def _edited_from_controls(self, original: ColorCycleRange) -> ColorCycleRange:
        return original.edited(
            rate=self._rate.value(),
            low=self._low.value(),
            high=self._high.value(),
            active=self._active.isChecked(),
            reverse=self._direction.currentIndex() == 1,
        )

    def _apply_range(self) -> None:
        index = self._ranges.currentRow()
        if index < 0:
            return
        try:
            cycle = self._edited_from_controls(self.document.color_cycles[index])
            self.document = self.document.with_cycle_replaced(index, cycle)
        except IlbmPaletteError as exc:
            QMessageBox.warning(self, "Invalid CRNG range", str(exc))
            return
        self._refresh_ranges(index)
        self._refresh_preview()

    def _add_range(self) -> None:
        try:
            cycle = ColorCycleRange.create(
                rate=self._rate.value(),
                low=self._low.value(),
                high=self._high.value(),
                active=self._active.isChecked(),
                reverse=self._direction.currentIndex() == 1,
            )
            self.document = self.document.with_cycle_added(cycle)
        except IlbmPaletteError as exc:
            QMessageBox.warning(self, "Invalid CRNG range", str(exc))
            return
        self._refresh_ranges(len(self.document.color_cycles) - 1)

    def _remove_range(self) -> None:
        index = self._ranges.currentRow()
        if index >= 0:
            self.document = self.document.with_cycle_removed(index)
            self._refresh_ranges(max(0, index - 1))
            self._refresh_preview()

    def play(self) -> None:
        if not self._playing:
            self._origin = time.monotonic()
            self._playing = True
            self._timer.start()

    def pause(self) -> None:
        if self._playing:
            self._elapsed = self._current_elapsed()
            self._playing = False
            self._timer.stop()

    def restart(self) -> None:
        self._elapsed = 0.0
        self._origin = time.monotonic()
        self._refresh_preview()

    def _current_elapsed(self) -> float:
        if not self._playing:
            return self._elapsed
        return self._elapsed + (time.monotonic() - self._origin) * self._speed.value()

    def _refresh_preview(self) -> None:
        palette = self.document.palette
        assert palette is not None
        colors = palette_at(palette.colors, self.document.color_cycles, self._current_elapsed())
        self._swatches.clear()
        for index, color in enumerate(colors):
            self._swatches.addItem(str(index))
            self._swatches.item(index).setBackground(QColor(*color))
        if self._indexed is not None:
            image = render_indexed_preview(self._indexed, colors)
            raw = image.tobytes("raw", "RGBA")
            qimage = QImage(
                raw,
                image.width,
                image.height,
                image.width * 4,
                QImage.Format.Format_RGBA8888,
            ).copy()
            self._image.setPixmap(QPixmap.fromImage(qimage))

    def _save_as(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save ILBM with CRNG", self.source.name, "Amiga ILBM (*.iff *.ilbm *.lbm)"
        )
        if not filename:
            return
        output = Path(filename)
        overwrite = False
        if output.exists():
            overwrite = (
                QMessageBox.question(self, "Overwrite ILBM?", output.name)
                == QMessageBox.StandardButton.Yes
            )
            if not overwrite:
                return
        try:
            write_cycle_document(self.document, output, overwrite=overwrite)
        except (OSError, IlbmPaletteError) as exc:
            QMessageBox.critical(self, "Could not save ILBM", str(exc))
            return
        QMessageBox.information(self, "ILBM saved", str(output))
