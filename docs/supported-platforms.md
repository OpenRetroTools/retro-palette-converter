# Supported platforms

Retro Palette Converter currently includes palette support for:

- Amiga OCS, ECS, and AGA
- Commodore 64, VIC-20, and Plus/4
- Atari 2600/TIA, Atari 8-bit ANTIC/GTIA, ST, STE, and Falcon030
- Sinclair ZX Spectrum 48K and ZX Spectrum 128K
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
