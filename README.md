# Retro Palette Converter

A small cross-platform GUI and CLI for converting artwork to classic and
hardware-inspired retro palettes.

## Features

- Side-by-side original and converted previews
- Game Boy, PICO-8, EGA 16, DawnBringer 16, and Amiga OCS 16/32
- None or Floyd–Steinberg dithering
- PNG, JPEG, and BMP input; PNG output
- Alpha preservation
- Drag and drop, synchronized zoom, pan, fit, and 100% view
- Lightweight CLI without Qt

## Development installation

```bash
unset UV_INDEX_URL UV_DEFAULT_INDEX UV_EXTRA_INDEX_URL
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL
uv sync --extra dev --extra gui --default-index https://pypi.org/simple
```

## GUI

```bash
uv run retropal gui
```

Linux and ChromeOS Crostini users can use the included XCB launcher:

```bash
sudo apt install libxcb-cursor0
./scripts/run-gui-linux.sh
```

## CLI

```bash
uv run retropal palettes
uv run retropal inspect input.png
uv run retropal convert input.png --palette amiga-ocs-32 \
  --dither floyd-steinberg --output output.png
```

## Verification

```bash
uv run ruff format --check src tests
uv run ruff check .
uv run pytest
uv run python -m compileall -q src
```

## Roadmap

- v0.1: desktop converter and CLI
- v0.2: batch conversion
- v0.3: custom palette import and editing
- v0.4: sprite-sheet workflows

Licensed under the MIT License.

## Palette tools

- Palette preview with used-color count
- GPL and JSON palette export
- Amiga OCS `$RGB` metadata
