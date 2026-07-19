# Retro Palette Converter

A small cross-platform GUI and CLI for converting artwork to classic and
hardware-inspired retro palettes.

## Features

- Side-by-side original and converted previews
- Game Boy, PICO-8, EGA 16, DawnBringer 16, and Amiga OCS 16/32
- Atari 2600 (TIA), Atari 8-bit (ANTIC/GTIA), Atari ST, Atari STE, and Atari Falcon030
- None or Floyd–Steinberg dithering
- PNG, JPEG, and BMP input; PNG output
- Alpha preservation
- Drag and drop, synchronized zoom, pan, fit, and 100% view
- Batch conversion from both the GUI and CLI
- Visual dithering comparison with click-to-select previews
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

During development on ChromeOS/Crostini, install the XCB runtime and use the development launcher:

```bash
sudo apt install libxcb-cursor0
./scripts/run-gui-linux.sh
```

The packaged Linux release includes `RetroPaletteConverter.sh`. It detects
ChromeOS/Crostini and selects XCB only when required; ordinary Linux systems
continue to use Qt's default display backend.

## CLI

```bash
uv run retropal palettes
uv run retropal palettes --family Atari
uv run retropal palettes --verbose
uv run retropal inspect input.png
uv run retropal batch input-dir output-dir --palette amiga-ocs-32
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
- v0.3: custom palettes, palette interchange, import, and editing
- v0.4: sprite-sheet workflows

### M2.4 — Custom Palettes and Palette Interchange

M2.4 will establish a common palette model and interchange workflow for moving
palettes between Retro Palette Converter, Deluxe Paint, Personal Paint,
Brilliance, GrafX2, Godot2Amiga, and OpenVN. Import, export, conversion, and
validation will share the same palette data rather than relying on
application-specific GUI paths.

- **M2.4a Custom Palette Core** — create, edit, name, reorder, save, and load
  user-defined palettes through a shared core API suitable for both the GUI and
  CLI.
- **M2.4b Standard Palette Formats** — import and export GIMP Palette (GPL),
  JASC-PAL, RIFF PAL, Adobe Color Table (ACT), JSON, and CSV palettes while
  preserving colour order and available metadata.
- **M2.4c Indexed Image Palette Import** — extract embedded palettes from
  indexed PNG, GIF, and BMP images, including transparency information where
  the source format provides it.
- **M2.4d Amiga Palette Interchange** — read and write IFF/ILBM `CMAP` colour
  maps and `CRNG` colour-range metadata for interoperability with classic Amiga
  paint and animation workflows.
- **M2.4e Brilliance PLT Compatibility** — import and export Brilliance PLT
  palettes with documented compatibility behavior and round-trip tests.
- **M2.4f Palette Conversion and Validation** — convert between supported
  formats; validate colour counts, channel precision, duplicate colours,
  metadata, and target-format constraints; and report any lossy conversion
  before export.

### M2.5 — Amiga Colour Cycling

- Preview Amiga colour cycling in the palette panel and converted image.
- Create and edit cycling ranges, direction, rate, and active state.
- Preserve compatible cycling metadata during IFF/ILBM `CRNG` interchange.

Licensed under the MIT License.

## Palette tools

- Palette preview with used-color count
- GPL and JSON palette export
- Amiga OCS `$RGB` metadata

## Release builds

Linux:

```bash
./scripts/build-linux.sh
```

Windows PowerShell:

```powershell
./scripts/build-windows.ps1
```

Pushing a version tag such as `v0.1.2` runs the GitHub release workflow and
attaches Windows, Linux, and macOS Apple Silicon ZIP archives to the GitHub release.

### Extensible dithering

Dithering choices are provided by a shared registry used by both the CLI and desktop GUI.
Use **Tools → Compare Dithering…** after opening an image to preview several algorithms side by side and apply the preferred result.
M2.2a includes `none` and `floyd-steinberg`; additional algorithms can be registered without
changing command-line or GUI option lists.

## Dithering

Available modes: none, Floyd–Steinberg, Atkinson, Bayer 2×2, Bayer 4×4, Bayer 8×8, Sierra Lite, Sierra, Burkes, Stucki, and Jarvis–Judice–Ninke.


## Platform palettes

The built-in collection includes Amiga OCS/ECS/AGA, Commodore 64, VIC-20, Commodore Plus/4, Game Boy, EGA, PICO-8, DawnBringer 16, and the Atari platform pack (2600/TIA, 8-bit ANTIC/GTIA, ST, STE, Falcon030). Use `retropal palettes --verbose` to inspect metadata, or `retropal palettes --family Atari` to list one platform family.

### Atari platform pack (M2.3b) — historical accuracy notes

Real Atari hardware colour output varies by television standard (NTSC/PAL/SECAM), chip revision, analog encoder, emulator, or attached monitor, and in several cases no single "canonical" RGB table exists. Rather than presenting any one source as historically exact, each palette documents its basis in its metadata `description`:

- **`atari-2600-tia`** (128 colours, 16 hues × 8 luminances) — sourced from the Stella emulator's established NTSC reference table. The PAL TIA uses a different, non-equivalent hue layout and is not included.
- **`atari-8bit-antic-gtia`** (256 colours, 16 hues × 16 luminances) — a deterministic representative palette generated from a documented YUV colour-wheel decode, since no single canonical GTIA RGB table exists. SECAM units expose only 8 luminance levels (128 usable combinations).
- **`atari-st`** (16 colours) — a deterministic representative sample of the ST's 3-bit-per-channel hardware DAC (8×8×8 = **512 total colours**; 16 shown simultaneously in low resolution). Not a captured boot/desktop ROM palette, which varies by TOS version.
- **`atari-ste`** (16 colours) — the same representative hue layout at the STE's extended 4-bit-per-channel precision (16×16×16 = **4,096 total colours**; 16 shown simultaneously).
- **`atari-falcon030`** (256 colours) — an evenly stepped 8×8×4 sample of the Falcon030's 6-bit-per-channel hardware DAC (64×64×64 = **262,144 total colours**, 18-bit). This represents the indexed 256-colour palette mode only; the Falcon's separate 16-bit RGB565 true-colour mode (up to 65,536 simultaneous colours) is not an indexed palette and is not represented here.
