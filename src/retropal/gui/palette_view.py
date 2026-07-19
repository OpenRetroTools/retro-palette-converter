"""Compact palette swatch widget."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from retropal.palettes.base import RGBColor


class PaletteView(QWidget):
    """Display palette colors as a compact grid."""

    def __init__(self) -> None:
        super().__init__()
        self._colors: tuple[RGBColor, ...] = ()
        self.setMinimumHeight(52)

    def set_colors(self, colors: tuple[RGBColor, ...]) -> None:
        self._colors = colors
        self.update()

    @property
    def colors(self) -> tuple[RGBColor, ...]:
        """Return the colors currently displayed by the widget."""
        return self._colors

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API
        return QSize(320, 52)

    def paintEvent(self, event: object) -> None:  # noqa: N802 - Qt API
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().base())
        if not self._colors:
            return
        columns = min(16, max(1, len(self._colors)))
        rows = (len(self._colors) + columns - 1) // columns
        cell_width = max(1, self.width() // columns)
        cell_height = max(1, self.height() // rows)
        for index, color in enumerate(self._colors):
            column = index % columns
            row = index // columns
            painter.fillRect(
                column * cell_width,
                row * cell_height,
                cell_width,
                cell_height,
                QColor(*color),
            )
