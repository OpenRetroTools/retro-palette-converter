"""Zoomable image preview widget with drag-and-drop support."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPixmap, QWheelEvent
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}


class ImageView(QGraphicsView):
    """Pixel-friendly image view with fit, zoom and pan support."""

    file_dropped = Signal(object)
    zoom_requested = Signal(float)

    def __init__(self, placeholder: str, *, accept_drops: bool = False) -> None:
        super().__init__()
        self._scene = QGraphicsScene(self)
        self._item = QGraphicsPixmapItem()
        self._scene.addItem(self._item)
        self._has_image = False
        self.setScene(self._scene)
        self.setMinimumSize(280, 220)
        self.setAcceptDrops(accept_drops)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setToolTip(placeholder)
        self.setBackgroundBrush(QColor(72, 72, 72))

    def set_image(self, pixmap: QPixmap | None) -> None:
        self._item.setPixmap(pixmap or QPixmap())
        self._has_image = pixmap is not None and not pixmap.isNull()
        self._scene.setSceneRect(self._item.boundingRect())
        self.fit_image()

    def fit_image(self) -> None:
        if self._has_image:
            self.resetTransform()
            self.fitInView(self._item, Qt.AspectRatioMode.KeepAspectRatio)

    def zoom_actual_size(self) -> None:
        if self._has_image:
            self.resetTransform()

    def apply_zoom(self, factor: float) -> None:
        if self._has_image:
            self.scale(factor, factor)

    def zoom_in(self) -> None:
        self.apply_zoom(1.25)

    def zoom_out(self) -> None:
        self.apply_zoom(0.8)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.25 if event.angleDelta().y() > 0 else 0.8
            self.zoom_requested.emit(factor)
            event.accept()
            return
        super().wheelEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if self._first_image_path(event.mimeData().urls()) is not None:
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        path = self._first_image_path(event.mimeData().urls())
        if path is not None:
            self.file_dropped.emit(path)
            event.acceptProposedAction()

    @staticmethod
    def _first_image_path(urls: list) -> Path | None:
        for url in urls:
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES:
                    return path
        return None
