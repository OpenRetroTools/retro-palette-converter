"""Small editor for native custom palettes."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from retropal.palettes.custom import CustomPalette, CustomPaletteError
from retropal.palettes.native import NATIVE_SUFFIX, NativePaletteError
from retropal.palettes.store import CustomPaletteStore


class CustomPaletteDialog(QDialog):
    """Create, edit, persist, reopen, and choose custom palettes."""

    def __init__(self, store: CustomPaletteStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self.selected_palette_id: str | None = None
        self.setWindowTitle("Custom Palettes")
        self.resize(620, 420)
        self._build_ui()
        self._refresh_palettes()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        body = QHBoxLayout()
        self._palettes = QListWidget()
        self._palettes.currentRowChanged.connect(self._show_palette)
        body.addWidget(self._palettes, stretch=1)
        right = QVBoxLayout()
        self._title = QLabel("No custom palette selected")
        self._colors = QListWidget()
        right.addWidget(self._title)
        right.addWidget(self._colors, stretch=1)
        color_actions = QHBoxLayout()
        for label, callback in (
            ("Add…", self._add_color),
            ("Edit…", self._edit_color),
            ("Remove", self._remove_color),
            ("Up", lambda: self._move_color(-1)),
            ("Down", lambda: self._move_color(1)),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            color_actions.addWidget(button)
        right.addLayout(color_actions)
        body.addLayout(right, stretch=2)
        root.addLayout(body)

        palette_actions = QHBoxLayout()
        for label, callback in (
            ("New…", self._create_palette),
            ("Rename…", self._rename_palette),
            ("Open…", self._open_palette),
            ("Save", self._save_palette),
            ("Delete", self._delete_palette),
        ):
            button = QPushButton(label)
            button.clicked.connect(callback)
            palette_actions.addWidget(button)
        root.addLayout(palette_actions)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self._use_button = buttons.addButton("Use palette", QDialogButtonBox.ButtonRole.AcceptRole)
        self._use_button.clicked.connect(self._accept_selected)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _current(self) -> CustomPalette | None:
        item = self._palettes.currentItem()
        return self._store.get(item.data(Qt.ItemDataRole.UserRole)) if item is not None else None

    def _refresh_palettes(self, selected_id: str | None = None) -> None:
        self._palettes.clear()
        for palette in self._store.list():
            self._palettes.addItem(f"{palette.name} [{palette.id}]")
            self._palettes.item(self._palettes.count() - 1).setData(
                Qt.ItemDataRole.UserRole, palette.id
            )
        if self._palettes.count():
            row = 0
            if selected_id is not None:
                for index in range(self._palettes.count()):
                    if self._palettes.item(index).data(Qt.ItemDataRole.UserRole) == selected_id:
                        row = index
                        break
            self._palettes.setCurrentRow(row)
        else:
            self._show_palette()

    def _show_palette(self) -> None:
        palette = self._current()
        self._colors.clear()
        self._use_button.setEnabled(palette is not None)
        if palette is None:
            self._title.setText("No custom palette selected")
            return
        self._title.setText(f"{palette.name} · {len(palette.colors)} ordered colours")
        for index, color in enumerate(palette.colors):
            self._colors.addItem(f"{index:3d}   #{color[0]:02X}{color[1]:02X}{color[2]:02X}")

    def _replace(self, palette: CustomPalette, *, save: bool = True) -> None:
        self._store.replace(palette)
        if save:
            self._store.save(palette.id)
        self._refresh_palettes(palette.id)

    def _create_palette(self) -> None:
        palette_id, accepted = QInputDialog.getText(self, "New custom palette", "Stable ID:")
        if not accepted:
            return
        name, accepted = QInputDialog.getText(self, "New custom palette", "Name:")
        if not accepted:
            return
        try:
            palette = self._store.create(palette_id, name, ((0, 0, 0),))
            self._store.save(palette.id)
        except (OSError, CustomPaletteError) as exc:
            QMessageBox.critical(self, "Could not create palette", str(exc))
            return
        self._refresh_palettes(palette.id)

    def _rename_palette(self) -> None:
        palette = self._current()
        if palette is None:
            return
        name, accepted = QInputDialog.getText(
            self, "Rename custom palette", "Name:", text=palette.name
        )
        if accepted:
            try:
                self._replace(palette.rename(name))
            except (OSError, CustomPaletteError) as exc:
                QMessageBox.critical(self, "Could not rename palette", str(exc))

    def _choose_color(
        self, initial: tuple[int, int, int] = (0, 0, 0)
    ) -> tuple[int, int, int] | None:
        color = QColorDialog.getColor(QColor(*initial), self, "Choose palette colour")
        return (color.red(), color.green(), color.blue()) if color.isValid() else None

    def _add_color(self) -> None:
        palette = self._current()
        color = self._choose_color()
        if palette is not None and color is not None:
            self._replace(palette.add_color(color))
            self._colors.setCurrentRow(len(palette.colors))

    def _edit_color(self) -> None:
        palette = self._current()
        index = self._colors.currentRow()
        if palette is None or index < 0:
            return
        color = self._choose_color(palette.colors[index])
        if color is not None:
            self._replace(palette.set_color(index, color))
            self._colors.setCurrentRow(index)

    def _remove_color(self) -> None:
        palette = self._current()
        index = self._colors.currentRow()
        if palette is None or index < 0:
            return
        try:
            self._replace(palette.remove_color(index))
        except CustomPaletteError as exc:
            QMessageBox.warning(self, "Could not remove colour", str(exc))

    def _move_color(self, offset: int) -> None:
        palette = self._current()
        source = self._colors.currentRow()
        target = source + offset
        if palette is None or source < 0 or not 0 <= target < len(palette.colors):
            return
        self._replace(palette.move_color(source, target))
        self._colors.setCurrentRow(target)

    def _save_palette(self) -> None:
        palette = self._current()
        if palette is None:
            return
        try:
            path = self._store.save(palette.id)
        except OSError as exc:
            QMessageBox.critical(self, "Could not save palette", str(exc))
            return
        self._title.setText(f"Saved {path.name}")

    def _open_palette(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open native custom palette", "", f"RetroPal native palette (*{NATIVE_SUFFIX})"
        )
        if not filename:
            return
        try:
            palette = self._store.load(Path(filename))
            self._store.save(palette.id)
        except (OSError, CustomPaletteError, NativePaletteError) as exc:
            QMessageBox.critical(self, "Could not open palette", str(exc))
            return
        self._refresh_palettes(palette.id)

    def _delete_palette(self) -> None:
        palette = self._current()
        if palette is None:
            return
        if (
            QMessageBox.question(self, "Delete custom palette?", palette.name)
            != QMessageBox.StandardButton.Yes
        ):
            return
        try:
            self._store.delete(palette.id)
        except OSError as exc:
            QMessageBox.critical(self, "Could not delete palette", str(exc))
            return
        self._refresh_palettes()

    def _accept_selected(self) -> None:
        palette = self._current()
        if palette is not None:
            self.selected_palette_id = palette.id
            self.accept()
