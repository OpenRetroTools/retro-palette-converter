"""Compact palette swatch widget."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QGridLayout, QWidget

from retropal.palettes.base import RGBColor


class PaletteView(QWidget):
    """Display palette colors as a compact grid."""

    def __init__(self) -> None:
        super().__init__()
        self._colors: tuple[RGBColor, ...] = ()
        self._visible_colors: tuple[RGBColor, ...] = ()
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setHorizontalSpacing(0)
        self._layout.setVerticalSpacing(0)
        self.setMinimumHeight(52)

    def set_colors(self, colors: tuple[RGBColor, ...]) -> None:
        while (item := self._layout.takeAt(0)) is not None:
            if widget := item.widget():
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self._colors = colors
        self._visible_colors = self._sample_visible_colors(colors)
        for index, color in enumerate(self._visible_colors):
            swatch = QWidget(self)
            swatch.setObjectName(f"palette-swatch-{index}")
            swatch.setProperty("rgb", color)
            swatch.setAutoFillBackground(True)
            palette = swatch.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(*color))
            swatch.setPalette(palette)
            swatch.setMinimumSize(1, 1)
            self._layout.addWidget(swatch, index // 16, index % 16)
        self.repaint()

    @property
    def colors(self) -> tuple[RGBColor, ...]:
        """Return the colors currently displayed by the widget."""
        return self._colors

    @property
    def swatch_count(self) -> int:
        """Return the number of swatch widgets currently installed."""
        return self._layout.count()

    @property
    def visible_colors(self) -> tuple[RGBColor, ...]:
        """Return the deterministic subset represented by visible swatches."""
        return self._visible_colors

    @staticmethod
    def _sample_visible_colors(
        colors: tuple[RGBColor, ...], maximum: int = 256
    ) -> tuple[RGBColor, ...]:
        if len(colors) <= maximum:
            return colors
        return tuple(colors[index * (len(colors) - 1) // (maximum - 1)] for index in range(maximum))

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API
        return QSize(320, 52)
