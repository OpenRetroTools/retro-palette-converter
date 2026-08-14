"""Batch conversion dialog and background worker."""

from __future__ import annotations

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QThread, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from retropal.core.batch import BatchResult, convert_batch, discover_images
from retropal.core.dither import iter_dithers
from retropal.palettes import iter_palette_info


class BatchWorker(QObject):
    """Run a batch conversion without blocking the GUI thread."""

    progress = Signal(int, int, str)
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        palette_id: str,
        dither: str,
        *,
        recursive: bool,
        overwrite: bool,
        dry_run: bool,
    ) -> None:
        super().__init__()
        self._input_dir = input_dir
        self._output_dir = output_dir
        self._palette_id = palette_id
        self._dither = dither
        self._recursive = recursive
        self._overwrite = overwrite
        self._dry_run = dry_run
        self._cancelled = Event()

    def cancel(self) -> None:
        """Request cancellation at the next file boundary."""

        self._cancelled.set()

    @Slot()
    def run(self) -> None:
        """Perform conversion and emit a final result."""

        try:
            total = len(discover_images(self._input_dir, recursive=self._recursive))
            result = convert_batch(
                self._input_dir,
                self._output_dir,
                self._palette_id,
                self._dither,
                recursive=self._recursive,
                overwrite=self._overwrite,
                dry_run=self._dry_run,
                progress=lambda current, source: self.progress.emit(current, total, str(source)),
                is_cancelled=self._cancelled.is_set,
            )
        except (OSError, ValueError) as exc:
            self.failed.emit(str(exc))
        else:
            self.completed.emit(result)
        finally:
            self.finished.emit()


class DirectoryPicker(QWidget):
    """Line edit paired with a directory chooser button."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.line_edit = QLineEdit(self)
        button = QPushButton("Browse…", self)
        button.clicked.connect(self._browse)
        layout.addWidget(self.line_edit, stretch=1)
        layout.addWidget(button)

    def path(self) -> Path:
        return Path(self.line_edit.text()).expanduser()

    @Slot()
    def _browse(self) -> None:
        start = self.line_edit.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, self._title, start)
        if selected:
            self.line_edit.setText(selected)


class BatchConvertDialog(QDialog):
    """Configure and run a directory batch conversion."""

    def __init__(self, parent: QWidget | None = None, *, start_dir: Path | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Batch Convert")
        self.resize(640, 360)
        self._thread: QThread | None = None
        self._worker: BatchWorker | None = None
        self._result: BatchResult | None = None
        self._build_ui(start_dir or Path.home())

    def _build_ui(self, start_dir: Path) -> None:
        root = QVBoxLayout(self)
        form = QFormLayout()

        self._input_picker = DirectoryPicker("Select input directory", self)
        self._input_picker.line_edit.setText(str(start_dir))
        form.addRow("Input directory:", self._input_picker)

        self._output_picker = DirectoryPicker("Select output directory", self)
        self._output_picker.line_edit.setText(str(start_dir / "converted"))
        form.addRow("Output directory:", self._output_picker)

        self._palette_combo = QComboBox(self)
        for info in iter_palette_info():
            self._palette_combo.addItem(info.name, info.id)
        self._palette_combo.setCurrentIndex(self._palette_combo.findData("amiga-ocs-32"))
        form.addRow("Palette:", self._palette_combo)

        self._dither_combo = QComboBox(self)
        for algorithm in iter_dithers():
            self._dither_combo.addItem(algorithm.display_name, algorithm.id)
        form.addRow("Dithering:", self._dither_combo)

        self._recursive = QCheckBox("Include subdirectories", self)
        self._recursive.setChecked(True)
        form.addRow("", self._recursive)

        self._overwrite = QCheckBox("Overwrite existing output files", self)
        form.addRow("", self._overwrite)

        self._dry_run = QCheckBox("Dry run (write no files)", self)
        form.addRow("", self._dry_run)
        root.addLayout(form)

        self._status = QLabel("Ready", self)
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        self._progress = QProgressBar(self)
        self._progress.setRange(0, 1)
        self._progress.setValue(0)
        root.addWidget(self._progress)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        self._run_button = self._buttons.addButton("Run", QDialogButtonBox.ButtonRole.AcceptRole)
        self._cancel_button = self._buttons.addButton(
            "Cancel job", QDialogButtonBox.ButtonRole.RejectRole
        )
        self._cancel_button.setEnabled(False)
        self._open_output_button = self._buttons.addButton(
            "Open output", QDialogButtonBox.ButtonRole.ActionRole
        )
        self._open_output_button.setEnabled(False)
        self._run_button.clicked.connect(self._start)
        self._cancel_button.clicked.connect(self._cancel)
        self._open_output_button.clicked.connect(self._open_output)
        self._buttons.rejected.connect(self.reject)
        root.addWidget(self._buttons)

    @Slot()
    def _start(self) -> None:
        input_dir = self._input_picker.path()
        output_dir = self._output_picker.path()
        if not input_dir.is_dir():
            QMessageBox.warning(self, "Invalid input", "Select an existing input directory.")
            return
        if input_dir.resolve() == output_dir.resolve():
            QMessageBox.warning(
                self,
                "Invalid output",
                "The output directory must differ from the input directory.",
            )
            return

        self._result = None
        self._set_running(True)
        self._progress.setRange(0, 0)
        self._status.setText("Discovering images…")

        thread = QThread(self)
        worker = BatchWorker(
            input_dir,
            output_dir,
            self._palette_combo.currentData(),
            self._dither_combo.currentData(),
            recursive=self._recursive.isChecked(),
            overwrite=self._overwrite.isChecked(),
            dry_run=self._dry_run.isChecked(),
        )
        self._thread = thread
        self._worker = worker
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.completed.connect(self._on_completed)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._thread_finished)
        thread.start()

    @Slot(int, int, str)
    def _on_progress(self, current: int, total: int, source: str) -> None:
        self._progress.setRange(0, max(total, 1))
        self._progress.setValue(current)
        self._status.setText(f"{current} / {total} · {Path(source).name}")

    @Slot(object)
    def _on_completed(self, result: BatchResult) -> None:
        self._result = result
        label = "Cancelled" if result.cancelled else "Completed"
        self._status.setText(
            f"{label}: {len(result.converted)} converted, "
            f"{len(result.skipped)} skipped, {len(result.failures)} failed."
        )
        self._open_output_button.setEnabled(not self._dry_run.isChecked())
        if result.failures:
            details = "\n".join(
                f"{failure.source.name}: {failure.message}" for failure in result.failures[:10]
            )
            QMessageBox.warning(self, "Batch completed with errors", details)

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._status.setText("Batch conversion failed.")
        QMessageBox.critical(self, "Batch conversion failed", message)

    @Slot()
    def _thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_running(False)

    @Slot()
    def _cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self._cancel_button.setEnabled(False)
            self._status.setText("Cancelling after the current file…")

    @Slot()
    def _open_output(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._output_picker.path().resolve())))

    def _set_running(self, running: bool) -> None:
        self._run_button.setEnabled(not running)
        self._cancel_button.setEnabled(running)
        self._buttons.button(QDialogButtonBox.StandardButton.Close).setEnabled(not running)
        for widget in (
            self._input_picker,
            self._output_picker,
            self._palette_combo,
            self._dither_combo,
            self._recursive,
            self._overwrite,
            self._dry_run,
        ):
            widget.setEnabled(not running)

    def reject(self) -> None:
        if self._thread is not None:
            self._cancel()
            return
        super().reject()
