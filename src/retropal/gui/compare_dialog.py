"""Dialog for comparing multiple dithering algorithms."""

from __future__ import annotations

from collections.abc import Iterable

from PIL import Image
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from retropal.core.converter import convert
from retropal.core.dither import get_dither, iter_dithers
from retropal.palettes.base import RGBColor

DEFAULT_COMPARE_IDS = (
    "none",
    "floyd-steinberg",
    "atkinson",
    "bayer-4x4",
    "sierra",
    "stucki",
)
MAX_COMPARE_ALGORITHMS = 9
PREVIEW_MAX_SIZE = 320


def selected_compare_ids(checked_ids: Iterable[str]) -> tuple[str, ...]:
    """Validate and preserve registry order for selected algorithm identifiers."""

    selected = set(checked_ids)
    ordered = tuple(algorithm.id for algorithm in iter_dithers() if algorithm.id in selected)
    if not ordered:
        raise ValueError("Select at least one dithering algorithm")
    if len(ordered) > MAX_COMPARE_ALGORITHMS:
        raise ValueError(f"Select at most {MAX_COMPARE_ALGORITHMS} dithering algorithms")
    return ordered


class PreviewButton(QPushButton):
    """Clickable image preview that carries a dithering identifier."""

    chosen = Signal(str)

    def __init__(self, dither_id: str, title: str, pixmap: QPixmap, parent: QWidget) -> None:
        super().__init__(parent)
        self._dither_id = dither_id
        self.setCheckable(True)
        self.setText(title)
        self.setIcon(pixmap)
        self.setIconSize(pixmap.size())
        self.setMinimumWidth(PREVIEW_MAX_SIZE + 24)
        self.setToolTip(f"Choose {title}")
        self.clicked.connect(self._emit_choice)

    def _emit_choice(self) -> None:
        self.chosen.emit(self._dither_id)


class CompareDitheringDialog(QDialog):
    """Render several dithering variants and let the user choose one."""

    def __init__(
        self,
        source_image: Image.Image,
        palette_id: str,
        current_dither_id: str,
        parent: QWidget | None = None,
        *,
        colors: tuple[RGBColor, ...] | None = None,
    ) -> None:
        super().__init__(parent)
        self._source_image = source_image.copy()
        self._palette_id = palette_id
        self._colors = colors
        self.selected_dither_id = current_dither_id
        self._checks: dict[str, QCheckBox] = {}
        self._preview_buttons: dict[str, PreviewButton] = {}
        self.setWindowTitle("Compare Dithering")
        self.resize(1120, 780)
        self._build_ui(current_dither_id)
        self._render_previews()

    def _build_ui(self, current_dither_id: str) -> None:
        root = QVBoxLayout(self)
        intro = QLabel(
            "Select up to nine algorithms, refresh the previews, then click the result "
            "you want to use."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        options_group = QGroupBox("Algorithms")
        options = QGridLayout(options_group)
        defaults = set(DEFAULT_COMPARE_IDS) | {current_dither_id}
        for index, algorithm in enumerate(iter_dithers()):
            checkbox = QCheckBox(algorithm.display_name)
            checkbox.setChecked(algorithm.id in defaults)
            self._checks[algorithm.id] = checkbox
            options.addWidget(checkbox, index // 4, index % 4)
        root.addWidget(options_group)

        controls = QHBoxLayout()
        refresh_button = QPushButton("Refresh previews")
        refresh_button.clicked.connect(self._render_previews)
        controls.addWidget(refresh_button)
        controls.addStretch()
        self._selection_label = QLabel()
        controls.addWidget(self._selection_label)
        root.addLayout(controls)

        self._preview_widget = QWidget()
        self._preview_grid = QGridLayout(self._preview_widget)
        self._preview_grid.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._preview_widget)
        root.addWidget(scroll, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self._update_selection_label()

    def _checked_ids(self) -> tuple[str, ...]:
        return tuple(dither_id for dither_id, check in self._checks.items() if check.isChecked())

    def _clear_previews(self) -> None:
        while self._preview_grid.count():
            item = self._preview_grid.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._preview_buttons.clear()

    def _render_previews(self) -> None:
        try:
            dither_ids = selected_compare_ids(self._checked_ids())
        except ValueError as exc:
            QMessageBox.warning(self, "Cannot compare dithering", str(exc))
            return

        self._clear_previews()
        source = self._preview_source()
        columns = 3 if len(dither_ids) > 4 else 2
        for index, dither_id in enumerate(dither_ids):
            algorithm = get_dither(dither_id)
            result = convert(source, self._palette_id, dither_id, colors=self._colors)
            button = PreviewButton(
                dither_id,
                algorithm.display_name,
                self._pil_to_pixmap(result),
                self._preview_widget,
            )
            button.setChecked(dither_id == self.selected_dither_id)
            button.chosen.connect(self._choose)
            self._preview_buttons[dither_id] = button
            self._preview_grid.addWidget(button, index // columns, index % columns)

    def _preview_source(self) -> Image.Image:
        source = self._source_image.copy()
        source.thumbnail((PREVIEW_MAX_SIZE, PREVIEW_MAX_SIZE), Image.Resampling.LANCZOS)
        return source

    def _choose(self, dither_id: str) -> None:
        self.selected_dither_id = dither_id
        for candidate_id, button in self._preview_buttons.items():
            button.setChecked(candidate_id == dither_id)
        self._update_selection_label()

    def _update_selection_label(self) -> None:
        display_name = get_dither(self.selected_dither_id).display_name
        self._selection_label.setText(f"Selected: {display_name}")

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
