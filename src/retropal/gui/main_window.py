"""Main window for Retro Palette Converter."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QSettings, QSignalBlocker, Qt
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
from retropal.core.dither import iter_dithers
from retropal.gui.batch_dialog import BatchConvertDialog
from retropal.gui.compare_dialog import CompareDitheringDialog
from retropal.gui.controller import ConverterController, palette_display_metadata
from retropal.gui.image_view import ImageView
from retropal.gui.palette_view import PaletteView
from retropal.palettes import get_palette_info, iter_palette_info
from retropal.palettes.fixed import load_fixed_palette
from retropal.palettes.profiles import get_platform_profile, iter_platform_profiles

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp)"


class MainWindow(QMainWindow):
    """Release-candidate desktop interface."""

    def __init__(self) -> None:
        super().__init__()
        self._controller = ConverterController()
        self._settings = QSettings()
        self.setAcceptDrops(True)
        self.setWindowTitle("Retro Palette Converter")
        self.resize(1100, 700)
        self.setStatusBar(QStatusBar(self))
        self._build_actions()
        self._build_toolbar()
        self._build_content()
        self._set_conversion_enabled(False)

    def _build_actions(self) -> None:
        self._open_action = QAction("&Open…", self)
        self._open_action.setShortcut(QKeySequence.StandardKey.Open)
        self._open_action.triggered.connect(self.open_image)

        self._export_action = QAction("&Save As…", self)
        self._export_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        self._export_action.triggered.connect(self.export_image)

        self._batch_action = QAction("&Batch Convert…", self)
        self._batch_action.triggered.connect(self.open_batch_dialog)

        self._compare_action = QAction("&Compare Dithering…", self)
        self._compare_action.triggered.connect(self.open_compare_dialog)

        self._export_palette_action = QAction("Export &Palette…", self)
        self._export_palette_action.triggered.connect(self.export_palette)

        quit_action = QAction("E&xit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)

        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self._open_action)
        file_menu.addAction(self._batch_action)
        file_menu.addAction(self._export_action)
        file_menu.addAction(self._export_palette_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(self._compare_action)
        self.menuBar().addMenu("&Help").addAction(about_action)

    def _build_toolbar(self) -> None:
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.addAction(self._open_action)
        toolbar.addAction(self._export_action)
        toolbar.addSeparator()

        for label, callback, shortcut in (
            ("Fit", self._fit_views, None),
            ("100%", self._actual_size_views, None),
            ("Zoom out", self._zoom_out_views, QKeySequence.StandardKey.ZoomOut),
            ("Zoom in", self._zoom_in_views, QKeySequence.StandardKey.ZoomIn),
        ):
            action = QAction(label, self)
            if shortcut is not None:
                action.setShortcut(shortcut)
            action.triggered.connect(callback)
            toolbar.addAction(action)

    def _build_content(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)
        previews = QHBoxLayout()
        self._original_view = ImageView("Drop an image here", accept_drops=True)
        self._converted_view = ImageView("Converted preview")
        self._original_view.file_dropped.connect(self.load_path)
        self._original_view.zoom_requested.connect(self._zoom_views)
        self._converted_view.zoom_requested.connect(self._zoom_views)
        previews.addWidget(self._preview_group("Original", self._original_view))
        previews.addWidget(self._preview_group("Converted", self._converted_view))
        root.addLayout(previews, stretch=1)

        controls = QHBoxLayout()
        form = QFormLayout()
        self._profile_combo = QComboBox()
        self._profile_combo.addItem("All platforms", None)
        for profile in iter_platform_profiles():
            self._profile_combo.addItem(profile.name, profile.id)
        form.addRow("Profile:", self._profile_combo)

        self._palette_combo = QComboBox()
        self._populate_palette_combo()
        self._palette_combo.setCurrentIndex(self._palette_combo.findData("amiga-ocs-32"))
        self._profile_combo.currentIndexChanged.connect(self._apply_platform_profile)
        self._palette_combo.currentIndexChanged.connect(self.refresh_conversion)
        if os.environ.get("RETROPAL_PALETTE_TRACE"):
            self._profile_combo.currentIndexChanged.connect(
                lambda: self._trace_palette("profileCurrentIndexChanged")
            )
            self._palette_combo.currentIndexChanged.connect(
                lambda: self._trace_palette("currentIndexChanged")
            )
            self._palette_combo.currentTextChanged.connect(
                lambda: self._trace_palette("currentTextChanged")
            )
            self._palette_combo.activated.connect(lambda: self._trace_palette("activated"))
        form.addRow("Palette:", self._palette_combo)

        self._dither_combo = QComboBox()
        for algorithm in iter_dithers():
            self._dither_combo.addItem(algorithm.display_name, algorithm.id)
        self._dither_combo.currentIndexChanged.connect(self.refresh_conversion)
        form.addRow("Dithering:", self._dither_combo)
        controls.addLayout(form)
        controls.addStretch()
        self._image_info = QLabel("No image loaded")
        self._image_info.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        controls.addWidget(self._image_info)
        self._export_button = QPushButton("Save As…")
        self._export_button.clicked.connect(self.export_image)
        controls.addWidget(self._export_button)
        root.addLayout(controls)

        palette_row = QHBoxLayout()
        self._palette_view = PaletteView()
        self._palette_metadata = QLabel("No palette generated")
        self._palette_metadata.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        palette_row.addWidget(self._palette_view, stretch=1)
        palette_row.addWidget(self._palette_metadata)
        root.addLayout(palette_row)
        self.setCentralWidget(central)

    def _populate_palette_combo(self, palette_ids: tuple[str, ...] | None = None) -> None:
        allowed = set(palette_ids) if palette_ids is not None else None
        palette_names: set[str] = set()
        added_palette_ids: set[str] = set()
        for info in iter_palette_info():
            if allowed is not None and info.id not in allowed:
                continue
            if info.name in palette_names:
                raise ValueError(f"Duplicate palette display name: {info.name}")
            if info.id in added_palette_ids:
                raise ValueError(f"Duplicate palette ID: {info.id}")
            palette_names.add(info.name)
            added_palette_ids.add(info.id)
            self._palette_combo.addItem(info.name, info.id)

    def _apply_platform_profile(self) -> None:
        profile_id = self._profile_combo.currentData()
        with QSignalBlocker(self._palette_combo):
            self._palette_combo.clear()
            if profile_id is None:
                self._populate_palette_combo()
                palette_id = self._controller.palette_id
            else:
                profile = get_platform_profile(profile_id)
                self._populate_palette_combo(profile.palette_ids)
                palette_id = profile.default_palette_id
            index = self._palette_combo.findData(palette_id)
            self._palette_combo.setCurrentIndex(index if index >= 0 else 0)
        self.refresh_conversion()

    @staticmethod
    def _preview_group(title: str, view: ImageView) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.addWidget(view)
        return group

    def open_image(self) -> None:
        start_dir = self._settings.value("lastDirectory", str(Path.home()), type=str)
        filename, _ = QFileDialog.getOpenFileName(self, "Open image", start_dir, IMAGE_FILTER)
        if filename:
            self.load_path(Path(filename))

    def open_batch_dialog(self) -> None:
        start_dir = Path(self._settings.value("lastDirectory", str(Path.home()), type=str))
        dialog = BatchConvertDialog(self, start_dir=start_dir)
        dialog.exec()

    def open_compare_dialog(self) -> None:
        if self._controller.source_image is None:
            return
        current_dither = self._dither_combo.currentData()
        dialog = CompareDitheringDialog(
            self._controller.source_image,
            self._palette_combo.currentData(),
            current_dither,
            self,
        )
        if dialog.exec() != dialog.DialogCode.Accepted:
            return
        index = self._dither_combo.findData(dialog.selected_dither_id)
        if index >= 0:
            self._dither_combo.setCurrentIndex(index)

    def load_path(self, path: Path) -> None:
        try:
            source = self._controller.load(path)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, "Could not open image", str(exc))
            return
        self._settings.setValue("lastDirectory", str(path.parent))
        self._original_view.set_image(self._pil_to_pixmap(source))
        self._image_info.setText(f"{source.width} × {source.height} · {source.mode}")
        self._set_conversion_enabled(True)
        self.refresh_conversion()
        self.statusBar().showMessage(f"Opened {path.name}", 3000)

    def refresh_conversion(self) -> None:
        if not self._controller.has_image:
            return
        try:
            self._controller.set_options(
                self._palette_combo.currentData(),
                self._dither_combo.currentData(),
            )
            converted = self._controller.refresh()
        except ValueError as exc:
            QMessageBox.critical(self, "Conversion failed", str(exc))
            return
        self._converted_view.set_image(self._pil_to_pixmap(converted))
        self._refresh_palette_panel()
        self._trace_palette("rendered")
        self.statusBar().showMessage(
            f"Ready · {self._palette_combo.currentText()} · {self._dither_combo.currentText()}"
        )

    def _refresh_palette_panel(self) -> None:
        colors = self._controller.display_palette
        self._palette_view.set_colors(colors)
        self._palette_metadata.setText(
            palette_display_metadata(self._controller.palette_id, colors)
        )

    def _trace_palette(self, signal: str) -> None:
        if not os.environ.get("RETROPAL_PALETTE_TRACE"):
            return
        palette_id = self._palette_combo.currentData()
        palette = (
            get_palette_info(palette_id)
            if get_palette_info(palette_id).adaptive
            else load_fixed_palette(palette_id)
        )
        converted = self._controller.converted_image
        pixmap = self._converted_view.pixmap()
        qimage = pixmap.toImage()
        visible_checksum = hashlib.sha256(
            bytes(qimage.constBits()) if not qimage.isNull() else b""
        ).hexdigest()
        pil_checksum = (
            hashlib.sha256(converted.tobytes()).hexdigest() if converted is not None else ""
        )
        print(
            "PALETTE_TRACE",
            f"signal={signal}",
            f"combo_index={self._palette_combo.currentIndex()}",
            f"combo_text={self._palette_combo.currentText()!r}",
            f"combo_data={palette_id!r}",
            f"selected_id={self._controller.palette_id!r}",
            f"window_id={id(self)}",
            f"controller_id={id(self._controller)}",
            f"preview_widget_id={id(self._converted_view)}",
            f"palette_object_id={id(palette)}",
            f"palette_object_type={type(palette).__name__}",
            f"conversion_palette_id={self._controller.palette_id!r}",
            f"pil_mode={converted.mode if converted is not None else None!r}",
            f"pil_checksum={pil_checksum}",
            f"qimage_checksum={visible_checksum}",
            f"pixmap_cache_key={pixmap.cacheKey()}",
            f"visible_preview_checksum={visible_checksum}",
            f"swatch_rgb={self._palette_view.colors!r}",
            f"swatch_count={self._palette_view.swatch_count}",
            flush=True,
        )

    def export_image(self) -> None:
        if self._controller.converted_image is None:
            return
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save converted PNG",
            str(self._controller.suggested_output_path()),
            "PNG images (*.png)",
        )
        if not filename:
            return
        output = Path(filename)
        if output.suffix.lower() != ".png":
            output = output.with_suffix(".png")
        if output.exists():
            answer = QMessageBox.question(
                self,
                "Overwrite file?",
                f"{output.name} already exists. Overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        try:
            output = self._controller.export(output)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save image", str(exc))
            return
        self.statusBar().showMessage(f"Saved {output}", 5000)

    def export_palette(self) -> None:
        if not self._controller.result_palette:
            return
        suggested = self._controller.suggested_output_path().with_suffix(".gpl")
        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export palette",
            str(suggested),
            "GIMP Palette (*.gpl);;JSON palette (*.json)",
        )
        if not filename:
            return
        output = Path(filename)
        if output.suffix.lower() not in {".gpl", ".json"}:
            output = output.with_suffix(".json" if "JSON" in selected_filter else ".gpl")
        try:
            self._controller.export_palette(output)
        except (OSError, ValueError, RuntimeError) as exc:
            QMessageBox.critical(self, "Could not export palette", str(exc))
            return
        self.statusBar().showMessage(f"Saved palette {output}", 5000)

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Retro Palette Converter",
            f"Retro Palette Converter {__version__}\n\n"
            "Open-source retro image palette conversion.\n"
            "Copyright © OpenRetroTools\nMIT License",
        )

    def _set_conversion_enabled(self, enabled: bool) -> None:
        self._palette_combo.setEnabled(enabled)
        self._profile_combo.setEnabled(enabled)
        self._dither_combo.setEnabled(enabled)
        self._export_button.setEnabled(enabled)
        self._export_action.setEnabled(enabled)
        self._export_palette_action.setEnabled(enabled)
        self._compare_action.setEnabled(enabled)

    def _fit_views(self) -> None:
        self._original_view.fit_image()
        self._converted_view.fit_image()

    def _actual_size_views(self) -> None:
        self._original_view.zoom_actual_size()
        self._converted_view.zoom_actual_size()

    def _zoom_views(self, factor: float) -> None:
        self._original_view.apply_zoom(factor)
        self._converted_view.apply_zoom(factor)

    def _zoom_in_views(self) -> None:
        self._zoom_views(1.25)

    def _zoom_out_views(self) -> None:
        self._zoom_views(0.8)

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
