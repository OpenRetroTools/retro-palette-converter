# Retro Palette Converter

A small, deterministic command-line tool for converting PNG images to retro color palettes.
M1 provides the reusable conversion engine and CLI. The desktop GUI is planned for M2.

## Features

- Game Boy, PICO-8, EGA 16, and DawnBringer 16 fixed palettes
- Image-derived Amiga OCS 16- and 32-color palettes
- No dithering or Floyd-Steinberg dithering
- Preserves per-pixel alpha
- PNG inspection command
- Cross-platform Python package

## Install for development

```bash
unset UV_INDEX_URL UV_DEFAULT_INDEX UV_EXTRA_INDEX_URL
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL
uv sync --extra dev --default-index https://pypi.org/simple
```

The M1 CLI does not require Qt. PySide6 is deferred to the optional GUI dependency:

```bash
uv sync --extra gui --extra dev --default-index https://pypi.org/simple
```

## Usage

```bash
uv run retropal palettes
uv run retropal inspect input.png
uv run retropal convert input.png --palette gameboy --output output.png
uv run retropal convert input.png --palette amiga-ocs-32 \
  --dither floyd-steinberg --output output.png
```

Available palette IDs:

- `gameboy`
- `pico8`
- `ega`
- `dawnbringer16`
- `amiga-ocs-16`
- `amiga-ocs-32`

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run retropal --version
```

## Desktop GUI (M2)

Install the optional Qt dependency and start the application:

```bash
uv sync --extra dev --extra gui --default-index https://pypi.org/simple
uv run retropal gui
```

The GUI supports opening or dropping a PNG, side-by-side previews, palette and dithering
selection, and PNG export. The conversion engine remains usable without Qt through the CLI.

### Linux / ChromeOS Crostini

If the native Wayland backend is unstable, start the GUI through the included
XCB wrapper:

```bash
./scripts/run-gui-linux.sh
```

Set `QT_QPA_PLATFORM=wayland` explicitly to retry the native Wayland backend.
