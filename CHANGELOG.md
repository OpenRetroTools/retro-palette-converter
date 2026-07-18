## [Unreleased]

### Added

- Atkinson error-diffusion dithering.
- Bayer 2×2, 4×4, and 8×8 ordered dithering.

### Changed

- Refactored dithering into an extensible registry shared by the converter, CLI, and GUI.
- Kept the existing `none` and `floyd-steinberg` modes backward compatible.

# Changelog

## Unreleased

### Added

- Added a responsive GUI batch-conversion dialog under File → Batch Convert.
- Added input/output directory selection, palette and dithering options, recursive mode, overwrite, and dry-run controls.
- Added progress reporting, cancellation between files, output-folder opening, and completion summaries.
- Extended the shared batch engine with progress and cancellation hooks for GUI reuse.

## 0.1.2 — 2026-07-18

### Fixed

- Added a Crostini-aware Linux launcher to release packages.
- Use Qt's XCB backend automatically on ChromeOS/Crostini while leaving ordinary Linux unchanged.
- Made Linux ZIP post-processing safe when temporary files and the repository are on different filesystems.
- Added regression coverage for the packaged launcher and its executable permissions.

### Changed

- Updated Linux, ChromeOS, release, and itch.io documentation.
- Updated release workflow defaults and the release checklist for v0.1.2.

## 0.1.0 — 2026-07-18

- First public release.
- Added reproducible Windows and Linux packaging.
- Added GitHub release workflow and itch.io release material.
- Added palette preview and GPL/JSON palette export.

## 0.1.0rc2

- Display the colors actually used by the converted image.
- Export palettes as GPL and JSON.
- Show Amiga OCS 12-bit `$RGB` values.
- Improve palette export error handling.


## 0.1.0-rc1 — M4

- Polish the desktop interface for the first public release candidate.
- Add File and Help menus, toolbar actions, keyboard shortcuts, and About dialog.
- Add PNG, JPEG, and BMP input filters.
- Remember the last-used input directory.
- Add synchronized Ctrl+mouse-wheel zoom and synchronized toolbar zoom.
- Add overwrite confirmation and improved automatic output filenames.
- Add release-ready README and cross-platform CI verification.
- Keep the CLI independent of the optional Qt dependency.

## 0.4.0.dev0 — M3

- Added a Qt-independent conversion controller.
- Replaced label previews with zoomable and pannable graphics views.
- Added fit, 100%, zoom-in and zoom-out toolbar actions.
- Added an XCB launcher for Linux and ChromeOS Crostini.

## 0.3.0.dev0 — M2

- Added the minimal PySide6 GUI, live preview, drag-and-drop, and PNG export.

## 0.2.0.dev0 — M1

- Added PNG conversion, fixed palettes, Amiga OCS palettes, dithering, and inspection.
