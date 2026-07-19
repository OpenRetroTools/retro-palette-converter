"""Desktop application entry point."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Sequence
from pathlib import Path


def _run_palette_trace_sequence(application: object, window: object, image_path: Path) -> None:
    """Run the opt-in rendered-palette diagnostic inside the real application."""
    from PySide6.QtGui import QImage

    sequence = (
        "amiga-ocs-16",
        "commodore-64",
        "atari-st",
        "amiga-ocs-16",
        "commodore-64",
    )
    screenshot_dir = Path(
        os.environ.get("RETROPAL_PALETTE_SCREENSHOT_DIR", "palette-trace-screenshots")
    )
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    checksums = []
    try:
        window.load_path(image_path)
        application.processEvents()
        for step, palette_id in enumerate(sequence, start=1):
            index = window._palette_combo.findData(palette_id)
            if index < 0:
                raise RuntimeError(f"Palette is absent from combo box: {palette_id}")
            window._palette_combo.setCurrentIndex(index)
            application.processEvents()
            window.repaint()
            application.processEvents()
            image = (
                window._converted_view.pixmap()
                .toImage()
                .convertToFormat(QImage.Format.Format_RGBA8888)
            )
            checksum = hashlib.sha256(bytes(image.constBits())[: image.sizeInBytes()]).hexdigest()
            checksums.append(checksum)
            screenshot = screenshot_dir / f"packaged-step-{step}-{palette_id}.png"
            if not window.grab().save(str(screenshot)):
                raise RuntimeError(f"Could not save packaged GUI screenshot: {screenshot}")
            print(
                "PACKAGED_PALETTE_TRACE",
                f"step={step}",
                f"palette_id={palette_id}",
                f"visible_preview_checksum={checksum}",
                f"swatch_rgb={window._palette_view.colors!r}",
                f"swatch_count={window._palette_view.swatch_count}",
                flush=True,
            )
        if checksums[1] == checksums[0] or checksums[2] == checksums[0]:
            raise RuntimeError("Fixed-palette previews did not visibly differ from Amiga")
        if checksums[3] != checksums[0] or checksums[4] != checksums[1]:
            raise RuntimeError("Repeated palette selections were not deterministic")
    except Exception as exc:  # diagnostic boundary must return a failing status
        print(f"PACKAGED_PALETTE_TRACE error={exc}", flush=True)
        application.exit(1)
        return
    application.exit(0)


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
    application.setApplicationDisplayName("Retro Palette Converter")
    application.setOrganizationName("OpenRetroTools")
    application.setOrganizationDomain("github.com/OpenRetroTools")
    window = MainWindow()
    window.show()
    if trace_image := os.environ.get("RETROPAL_PALETTE_TRACE_IMAGE"):
        from PySide6.QtCore import QTimer

        QTimer.singleShot(
            0,
            lambda: _run_palette_trace_sequence(application, window, Path(trace_image)),
        )
    return application.exec()
