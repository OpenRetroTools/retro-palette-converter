# Supported platforms

Retro Palette Converter currently includes palette support for:

- Amiga OCS, ECS, and AGA
- Commodore 64, VIC-20, and Plus/4
- Atari 2600/TIA, Atari 8-bit ANTIC/GTIA, ST, STE, and Falcon030
- Sinclair ZX Spectrum 48K and ZX Spectrum 128K
- Nintendo Entertainment System, Game Boy, Game Boy Pocket, Game Boy Color,
  and Super Nintendo Entertainment System
- Sega Master System, Game Gear, and Mega Drive / Genesis
- IBM PC CGA, EGA, VGA 16, and VGA 256
- Apple Macintosh black-and-white and System 7-era 8-bit colour
- Hercules monochrome and Sharp X68000
- Game Boy, EGA, PICO-8, and DawnBringer 16

## Sinclair ZX Spectrum

Both Spectrum profiles provide three conversion modes:

- **Normal** — the eight colours at normal intensity.
- **Bright** — the eight colours with the BRIGHT bit enabled. Bright black is
  identical to normal black on the hardware.
- **Automatic Bright** — all 15 unique colours, allowing nearest-colour
  conversion to choose normal or bright intensity for each pixel.

The 48K and 128K use the same display palette. They remain separate platform
profiles so later model-specific display modes can be added without changing
saved palette IDs. Spectrum 8×8 attribute-cell ink, paper, and BRIGHT
restrictions are intentionally deferred to a future milestone.

## Nintendo

The Nintendo profiles provide display-palette conversion for NES, original
Game Boy (DMG), Game Boy Pocket, Game Boy Color, and Super NES. The Game Boy
Color and Super NES definitions are deterministic representative samples of
their programmable 15-bit, 32,768-colour spaces rather than claims that the
hardware has one fixed palette. The NES definition is a practical NTSC 2C02
RGB approximation; analog output and regional PPU variants differ.

This milestone does not emulate NES emphasis bits, Game Boy tile rules, Game
Boy Color palette banks, SNES colour math, or sprite/background priorities.

## Sega

The Sega platform pack provides the complete deterministic RGB display colour
spaces used as representative conversion palettes: 64 colours for Master
System (6-bit RGB), 4,096 for Game Gear (12-bit RGB), and 512 for Mega Drive /
Genesis (9-bit RGB). The palette panel shows a deterministic overview when a
palette is too large to display every swatch usefully, while conversion uses
the complete colour set.

These profiles do not emulate CRAM organization, shadow/highlight mode, sprite
priorities, palette animation, or Game Gear LCD characteristics.

## Classic computers and display standards

The classic display pack includes both standard fixed selections and
deterministic representative conversion palettes. CGA exposes its two common
high-intensity four-colour RGBI selections. EGA and VGA 16 use their canonical
default 16-colour mappings. VGA 256 uses a deterministic mode-13h-style colour
cube and grayscale ramp.

Classic Macintosh support includes the original one-bit black-and-white values
and a representative System 7-era 256-colour palette. Hercules uses logical
black and white, independent of monitor phosphor colour. The X68000 profile
provides a deterministic 256-colour sample of its programmable 15-bit display
space.

These are conversion palettes, not hardware emulators. CGA composite artifact
colours, VGA DAC programming, hardware gamma, QuickDraw behaviour, monitor
phosphor characteristics, and programmable display-mode constraints are
outside this milestone.
