# M2.3b — Atari Platform Pack

Adds five Atari hardware palettes to the existing data-driven palette
registry, following the exact conventions established in M2.3a: a JSON
definition file per palette in `src/retropal/palettes/definitions/`, an
entry in `fixed_palette_ids()`, and automatic pickup by `PALETTE_IDS`,
`retropal palettes`, and both GUI palette combo boxes (which are populated
directly from `PALETTE_IDS`, so no separate GUI registration step exists or
was needed).

## Palettes added

| Palette ID | Name | Colours | Basis |
|---|---|---|---|
| `atari-2600-tia` | Atari 2600 (TIA, NTSC) | 128 | Established reference: Stella emulator's NTSC TIA table |
| `atari-8bit-antic-gtia` | Atari 8-bit (ANTIC/GTIA) | 256 | Deterministic representative: YUV colour-wheel decode |
| `atari-st` | Atari ST | 16 | Deterministic representative sample of a 512-colour (3-bit/channel) space |
| `atari-ste` | Atari STE | 16 | Deterministic representative sample of a 4,096-colour (4-bit/channel) space |
| `atari-falcon030` | Atari Falcon030 | 256 | Deterministic 8×8×4 sample of a 262,144-colour (6-bit/channel) space |

All five share `family = "Atari"` and `manufacturer = "Atari"`, so
`retropal palettes --family Atari` lists exactly these five.

## Why these five are not presented as single "the historically exact" tables

Per the milestone's accuracy requirements, none of these are claimed as a
single canonical hardware capture:

- **TIA**: real NTSC TIA output varies by console revision and television;
  the PAL TIA additionally uses a different, non-equivalent hue layout,
  which is intentionally not folded into this palette.
- **ANTIC/GTIA**: there is no single canonical GTIA RGB table in wide
  community use — multiple incompatible "approximations" circulate. A
  deterministic, documented generation method is used instead, and SECAM
  units are noted as exposing only 8 (not 16) luminance levels.
- **ST / STE**: these use a true digital RGB DAC (no composite-video
  ambiguity), but the specific 16-colour palette resident in ROM at boot
  varies by TOS version, so a representative sample of the DAC's colour
  space is provided instead of claiming to reproduce any specific ROM
  table.
- **Falcon030**: the 256-colour entry represents only the indexed palette
  mode. The Falcon's much larger 65,536-colour RGB565 true-colour mode is
  a different, non-indexed colour mechanism and is documented as outside
  the scope of this palette rather than silently ignored.

Total hardware colour space is documented separately from the
simultaneously-displayable/representative palette size for every platform
where the two differ (ST: 512 total / 16 shown; STE: 4,096 total / 16
shown; Falcon030: 262,144 total / 256 indexed, plus a separate 65,536-colour
true-colour mode). See each palette's `description` field (via
`retropal palettes --verbose`) and the "Atari platform pack" section of the
top-level `README.md` for the full detail.

## CLI additions

- `retropal palettes --family <name>` — filter the palette listing (plain
  or `--verbose`) by family, case-insensitively. Works for every existing
  family (`Amiga`, `Commodore`, etc.), not just `Atari`.

## Applying and verifying

```bash
./.delivery/M2.3b/APPLY.sh
./.delivery/M2.3b/VERIFY.sh
```

See `APPLY.sh` for the overlay-extraction mechanism and `CHANGES.md` for
the full list of added/modified files.
