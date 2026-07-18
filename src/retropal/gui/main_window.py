"""Main window for Retro Palette Converter."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from retropal import __version__
from retropal.core.models import DitherMode
from retropal.gui.controller import ConverterController
from retropal.gui.image_view import ImageView
from retropal.palettes import PALETTE_IDS


class MainWindow(QMainWindow):
    """Minimal image conversion desktop interface."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = ConverterController()

        self.setWindowTitle("Retro Palette Converter")
        self.resize(1100, 700)
        self.setStatusBar(QStatusBar(self))
        self._build_actions()
        self._build_toolbar()
        self._build_content()
        self._set_conversion_enabled(False)

    def _build_actions(self) -> None:
        open_action = QAction("&Open PNG…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_image)

        export_action = QAction("&Export PNG…", self)
        export_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        export_action.triggered.connect(self.export_image)
        self._export_action = export_action

        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(open_action)
        file_menu.addAction(export_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        self.menuBar().addMenu("&Help").addAction(about_action)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("View")
        toolbar.setMovable(False)

        fit_action = QAction("Fit", self)
        fit_action.triggered.connect(self._fit_views)
        toolbar.addAction(fit_action)

        actual_action = QAction("100%", self)
        actual_action.triggered.connect(self._actual_size_views)
        toolbar.addAction(actual_action)

        zoom_out_action = QAction("Zoom out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._zoom_out_views)
        toolbar.addAction(zoom_out_action)

        zoom_in_action = QAction("Zoom in", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._zoom_in_views)
        toolbar.addAction(zoom_in_action)

    def _fit_views(self) -> None:
        self._original_view.fit_image()
        self._converted_view.fit_image()

    def _actual_size_views(self) -> None:
        self._original_view.zoom_actual_size()
        self._converted_view.zoom_actual_size()

    def _zoom_in_views(self) -> None:
        self._original_view.zoom_in()
        self._converted_view.zoom_in()

    def _zoom_out_views(self) -> None:
        self._original_view.zoom_out()
        self._converted_view.zoom_out()

    def _build_content(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)

        previews = QHBoxLayout()
        self._original_view = ImageView(
            "Drop a PNG here or choose File → Open",
            accept_drops=True,
        )
        self._original_view.file_dropped.connect(self.load_path)
        self._converted_view = ImageView("Converted preview")
        previews.addWidget(self._preview_group("Original", self._original_view))
        previews.addWidget(self._preview_group("Converted", self._converted_view))
        root.addLayout(previews, stretch=1)

        controls = QHBoxLayout()
        form = QFormLayout()
        self._palette_combo = QComboBox()
        self._palette_combo.addItems(PALETTE_IDS)
        self._palette_combo.setCurrentText("amiga-ocs-32")
        self._palette_combo.currentTextChanged.connect(self.refresh_conversion)
        form.addRow("Palette:", self._palette_combo)

        self._dither_combo = QComboBox()
        self._dither_combo.addItem("None", DitherMode.NONE)
        self._dither_combo.addItem("Floyd–Steinberg", DitherMode.FLOYD_STEINBERG)
        self._dither_combo.currentIndexChanged.connect(self.refresh_conversion)
        form.addRow("Dithering:", self._dither_combo)
        controls.addLayout(form)
        controls.addStretch()

        self._image_info = QLabel("No image loaded")
        self._image_info.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        controls.addWidget(self._image_info)

        self._export_button = QPushButton("Export PNG…")
        self._export_button.clicked.connect(self.export_image)
        controls.addWidget(self._export_button)
        root.addLayout(controls)

        self.setCentralWidget(central)

    @staticmethod
    def _preview_group(title: str, view: ImageView) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(view)
        return group

    def open_image(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open PNG",
            str(
                self._controller.source_path.parent if self._controller.source_path else Path.home()
            ),
            "PNG images (*.png)",
        )
        if filename:
            self.load_path(Path(filename))

    def load_path(self, path: Path) -> None:
        try:
            source = self._controller.load(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Could not open image", str(exc))
            return
        self._original_view.set_image(self._pil_to_pixmap(source))
        self._image_info.setText(f"{source.width} × {source.height} · RGBA")
        self._set_conversion_enabled(True)
        self.refresh_conversion()
        self.statusBar().showMessage(f"Opened {path.name}", 3000)

    def refresh_conversion(self) -> None:
        if not self._controller.has_image:
            return
        try:
            self._controller.set_options(
                self._palette_combo.currentText(),
                self._dither_combo.currentData(),
            )
            converted = self._controller.refresh()
        except ValueError as exc:
            QMessageBox.critical(self, "Conversion failed", str(exc))
            return
        self._converted_view.set_image(self._pil_to_pixmap(converted))

    def export_image(self) -> None:
        if self._controller.converted_image is None:
            return
        suggested = self._suggested_output_path()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export converted PNG",
            str(suggested),
            "PNG images (*.png)",
        )
        if not filename:
            return
        output = Path(filename)
        if output.suffix.lower() != ".png":
            output = output.with_suffix(".png")
        try:
            output = self._controller.export(output)
        except OSError as exc:
            QMessageBox.critical(self, "Could not export image", str(exc))
            return
        self.statusBar().showMessage(f"Exported {output}", 5000)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Retro Palette Converter",
            f"Retro Palette Converter {__version__}\n\n"
            "Convert PNG images to classic and hardware-inspired retro palettes.",
        )

    def _set_conversion_enabled(self, enabled: bool) -> None:
        self._palette_combo.setEnabled(enabled)
        self._dither_combo.setEnabled(enabled)
        self._export_button.setEnabled(enabled)
        self._export_action.setEnabled(enabled)

    def _suggested_output_path(self) -> Path:
        return self._controller.suggested_output_path()

    @staticmethod
    def _pil_to_pixmap(image: Image.Image) -> QPixmap:
        rgba = image.convert("RGBA")
        raw = rgba.tobytes("raw", "RGBA")
        qimage = QImage(
            raw,
            rgba.width,
            rgba.height,
            rgba.width * 4,
            QImage.Format.Format_RGBA8888,
        ).copy()
        return QPixmap.fromImage(qimage)
