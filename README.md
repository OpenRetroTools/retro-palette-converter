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
- Ordered custom palettes with native save/load and a compact GUI editor

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

If Crostini cannot be detected automatically, use the direct fallback:

```bash
QT_QPA_PLATFORM=xcb ./RetroPaletteConverter
```

## CLI

```bash
uv run retropal palettes
uv run retropal palettes --family Atari
uv run retropal palettes --verbose
uv run retropal inspect input.png
uv run retropal batch input-dir output-dir --palette amiga-ocs-32
uv run retropal convert input.png --palette amiga-ocs-32 \
  --dither floyd-steinberg --output output.png
uv run retropal custom-palettes create my-palette "My Palette" \
  '#000000' '#FFFFFF' '#000000'
uv run retropal custom-palettes show my-palette
uv run retropal convert input.png \
  --custom-palette ~/.local/share/retropal/palettes/my-palette.retropal-palette.json \
  --output output.png
```

## Verification

```bash
uv run ruff format --check src tests
uv run ruff check .
uv run basedpyright
uv run pytest
uv run python -m compileall -q src
```

## Roadmap

- v0.1: desktop converter and CLI
- v0.2: batch conversion
- v0.3: custom palettes, palette interchange, import, and editing
- v0.4: sprite-sheet workflows (original roadmap entry; scope deferred to 3.x)

Roadmap entries below describe plans, not claims of implemented or tested
compatibility.

### Completed 2.x milestones

- [x] **M2.1 Batch Conversion** — GUI and core batch conversion.
- [x] **M2.2 Dithering** — shared dithering registry, additional algorithms,
  and comparison previews; M2.2a established the extensible registry with
  `none` and `floyd-steinberg`.
- [x] **M2.3a Palette Metadata and Platform Profiles** — palette metadata plus
  Commodore and expanded Amiga profiles.
- [x] **M2.3b Atari Platform Pack** — Atari 2600, Atari 8-bit, ST, STE, and
  Falcon030 profiles.
- [x] **M2.3c Sinclair Platform Pack** — ZX Spectrum 48K and 128K profiles with
  normal, bright, and automatic-bright fixed palettes. Attribute-cell
  restrictions remain planned for a later milestone.
- [x] **M2.3d Nintendo Platform Pack** — NES, Game Boy, Game Boy Pocket, Game
  Boy Color, and Super NES display profiles. Hardware rendering restrictions
  remain planned for later milestones.
- [x] **M2.3e Sega Platform Pack** — Master System, Game Gear, and Mega Drive /
  Genesis representative display profiles using their deterministic RGB colour
  spaces.
- [x] **M2.3f Classic Computers and Display Standards Pack** — IBM CGA, EGA,
  VGA 16/256, classic Macintosh monochrome and 8-bit, Hercules monochrome, and
  Sharp X68000 representative display palettes.
- [x] **M2.3.9 Architecture and Quality Review** — automatic fixed-palette
  discovery, validated canonical metadata, cross-registry consistency checks,
  and generated platform/palette inventory.
- [x] **Pre-M2.4 Quality Hardening** — single-resolution palette data flow,
  static type checking in CI, and deterministic dithering regression coverage.

### M2.4 — Custom Palettes and Palette Interchange

Interchange work targets tested workflows with Deluxe Paint, Personal Paint,
Brilliance, GrafX2, Godot2Amiga, and OpenVN without claiming compatibility
before formats and round trips have been validated.

- [x] **M2.4a Custom Palette Core** — create, edit, name, reorder, save, and load
  user palettes through shared GUI and CLI services.
- **M2.4b Standard Palette Formats** — import and export GIMP GPL, JASC-PAL,
  RIFF PAL, Adobe ACT, JSON, and CSV while preserving colour order and supported
  metadata.
- **M2.4c Indexed Image Palette Import** — extract palettes and available
  transparency metadata from indexed PNG, GIF, and BMP images.
- **M2.4d Amiga Palette Interchange** — import and export IFF/ILBM `CMAP` and
  Amiga `CRNG` metadata.
- **M2.4e Brilliance PLT Compatibility** — add Brilliance PLT import and export
  after the format and round-trip behaviour have been validated.
- **M2.4f Palette Conversion and Validation** — convert supported formats;
  validate colour counts, channel precision, duplicates, metadata, and target
  platform limits; and report lossy conversions.

### M2.5 — Amiga Colour Cycling

- Read `CRNG` ranges; preview and edit range, direction, and speed; provide an
  animated preview; import and export cycle metadata; and preserve unrelated
  IFF chunks where practical.

### M2.6 — Palette Analysis

- Compare two palettes using exact and near-duplicate detection, shared and
  unique colours, RGB distance, luminance, and palette statistics.
- Add perceptual distance such as Delta E only with a documented colour-space
  and conversion method; raw RGB distance is not perceptual accuracy.
- Suggest palette reductions and merges, and validate platform limits.

### M2.7 — Palette Gallery and Library UX

- Add search; platform, family, and colour-count filters; tags; favourites;
  recently used palettes; grid/swatch previews; built-in versus user palette
  distinction; and source and licence metadata.

### M2.8 — Batch Processing and Automation

- Expand existing multi-file batch conversion with recursive folders,
  output-directory handling, filename templates, overwrite policy, CLI automation,
  machine-readable reports, conversion statistics, failure summaries, and
  deterministic non-interactive operation for CI and asset pipelines.

### Roadmap boundary

The 2.x phase focuses on palettes, palette interoperability, analysis,
browsing, and palette-based batch conversion. Sprite sheets, tile sets, fonts,
planar/bitplane asset export, and broader retro graphics tooling belong to a
later 3.x phase.

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

The built-in collection includes Amiga OCS/ECS/AGA, Commodore 64, VIC-20,
Commodore Plus/4, Game Boy, EGA, PICO-8, DawnBringer 16, the Atari platform
pack (2600/TIA, 8-bit ANTIC/GTIA, ST, STE, Falcon030), and Sinclair ZX
Spectrum 48K/128K profiles with normal, bright, and automatic-bright modes.
The Nintendo platform pack adds NES, Game Boy, Game Boy Pocket, Game Boy
Color, and Super NES display profiles.
The Sega platform pack adds Master System, Game Gear, and Mega Drive / Genesis
representative display profiles.
See [supported platforms](docs/supported-platforms.md). Use
`retropal palettes --verbose` to inspect metadata, or
`retropal palettes --family Sinclair` to list the Sinclair palettes.

### Atari platform pack (M2.3b) — historical accuracy notes

Real Atari hardware colour output varies by television standard (NTSC/PAL/SECAM), chip revision, analog encoder, emulator, or attached monitor, and in several cases no single "canonical" RGB table exists. Rather than presenting any one source as historically exact, each palette documents its basis in its metadata `description`:

- **`atari-2600-tia`** (128 colours, 16 hues × 8 luminances) — sourced from the Stella emulator's established NTSC reference table. The PAL TIA uses a different, non-equivalent hue layout and is not included.
- **`atari-8bit-antic-gtia`** (256 colours, 16 hues × 16 luminances) — a deterministic representative palette generated from a documented YUV colour-wheel decode, since no single canonical GTIA RGB table exists. SECAM units expose only 8 luminance levels (128 usable combinations).
- **`atari-st`** (16 colours) — a deterministic representative sample of the ST's 3-bit-per-channel hardware DAC (8×8×8 = **512 total colours**; 16 shown simultaneously in low resolution). Not a captured boot/desktop ROM palette, which varies by TOS version.
- **`atari-ste`** (16 colours) — the same representative hue layout at the STE's extended 4-bit-per-channel precision (16×16×16 = **4,096 total colours**; 16 shown simultaneously).
- **`atari-falcon030`** (256 colours) — an evenly stepped 8×8×4 sample of the Falcon030's 6-bit-per-channel hardware DAC (64×64×64 = **262,144 total colours**, 18-bit). This represents the indexed 256-colour palette mode only; the Falcon's separate 16-bit RGB565 true-colour mode (up to 65,536 simultaneous colours) is not an indexed palette and is not represented here.
