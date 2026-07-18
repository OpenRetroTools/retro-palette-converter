"""Desktop application entry point."""

from __future__ import annotations

from collections.abc import Sequence


def run_gui(argv: Sequence[str] | None = None) -> int:
    """Start the PySide6 desktop application."""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise RuntimeError(
            "The GUI dependencies are not installed. "
            "Run `uv sync --extra gui` or install retro-palette-converter[gui]."
        ) from exc

    from retropal.gui.main_window import MainWindow

    application = QApplication(list(argv) if argv is not None else [])
    application.setApplicationName("Retro Palette Converter")
    application.setOrganizationName("OpenRetroTools")
    window = MainWindow()
    window.show()
    return application.exec()
