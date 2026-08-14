# Brilliance PLT archaeology and compatibility

M2.4e deliberately provides **verified import only**. The available evidence
establishes a Brilliance palette-document variant well enough to extract its
register colours, but not well enough to write Brilliance gradient and range
state. Export therefore remains unsupported and is not advertised by the CLI
or GUI.

## Sources and corpus

- The original *Brilliance User's Guide*, version 1 (Digital Creations),
  documents palette load/save, 256 register colours, 128 gradient slots in
  eight ranges, pre-AGA 16-level channels, and AGA 256-level channels. A scan
  is hosted by [Retro Commodore](https://retro-commodore.eu/files/downloads/amigamanuals-xiik.net/Applications/Brilliance%20v1.0%20-%20Manual-ENG.pdf).
- [Aminet ArcsPack-12](https://www.aminet.net/package/pix/icon/ArcsPack-12)
  is a public 1995 archive whose readme says its palettes were created with
  Brilliance 2.0 and describes the files as IFF-like Brilliance palettes.
  Archive SHA-256:
  `7a7cc9a2cd663388b78678318feaf26f85ecbb7ebba4c28ad323f35ce6ea13fc`.
  All 17 palette files were inspected; they consistently use the supported
  structure below. Representative file SHA-256 values are:
  `Aquamarine` `b3083b9e52f6ea022c95d57282c149e5ab3ff269eeb4b53cc2d1ecd80c3b608c`,
  `Amber Haze` `3e75f38118a3a5a21a44fdf1fe11d10bac62539ad464fd9d2117ed548ee32ef9`,
  and `Raindrop` `1f5c564e8a73691f50189b133672bbb2c1b504f2e1a41d859c9e5b962d9c4db4`.
- Electronic Arts' IFF/ILBM rules and `CMAP` semantics are documented in
  [`amiga-palette-interchange.md`](amiga-palette-interchange.md). They establish
  big-endian chunk lengths, even-byte padding, and ordered RGB triples.

The historical files are not checked in. Tests use tiny synthetic documents
constructed only from the structure established by that corpus. The corpus
files are extensionless; `.plt` is accepted as the application-facing
extension, not asserted as an original filename requirement.

An unrelated modern ACE game-engine format also uses `.plt` for a packed
12-bit palette. No evidence connects it to Brilliance, and this implementation
intentionally does not accept it.

## Evidence table

| Position/field | Size/encoding | Meaning and allowed values | Evidence | Confidence |
| --- | --- | --- | --- | --- |
| Container | IFF `FORM`, big-endian lengths, type `ILBM` | Brilliance palette document container | all 17 samples; EA IFF rules | verified |
| First chunk | `ANNO` | exact Brilliance 1.0 or Release 2.0 writer annotation | all 17 samples | verified for supported variant |
| Second chunk | `CMAP`, 1152 bytes | 384 ordered 8-bit RGB triples | all 17 samples; ILBM `CMAP` | verified |
| `CMAP[0:256]` | 768 bytes | register palette slots | manual says 256 registers; corpus has 256 + 128 entries | strongly supported |
| `CMAP[256:384]` | 384 bytes | 128 gradient-slot colours | manual says 128 gradient slots; corpus remainder matches | strongly supported |
| Later chunks | `DRNG`, `CRNG`, `BRNG` | gradient/cycle state; zero or more | observed in corpus; field writer contract unresolved | verified presence, unknown serialization contract |
| RGB channels | one byte each | stored bytes are imported exactly | `CMAP`; corpus byte inspection | verified |
| pre-AGA precision | values in steps of 17 in examined palettes | 4-bit channels expanded to `n * 17` | manual and corpus | strongly supported; no normalization performed |
| active register count | no established field | which of 256 slots are active | absent from supported structure | unknown |
| export layout | entire document | required gradient/range relationships | no authoritative writer description or independent writer validation found | unknown; unsupported |

The key inference is the division of the 384 `CMAP` entries into the manual's
256 register slots followed by its 128 gradient slots. It is supported by two
independent kinds of evidence, but the codec reports the omitted gradient
slots rather than presenting this as lossless conversion.

## Supported import

The `brilliance-plt` codec accepts only a bounds-checked `FORM ILBM` document
with a recognized Brilliance 1.0/2.0 `ANNO`, followed immediately by a
384-entry `CMAP`, and only the observed Brilliance range/cycle chunk IDs after
it. This strict discriminator prevents arbitrary ILBM images or unrelated
`.plt` formats from being misidentified.

The first 256 entries become a normal `CustomPalette`. Order, duplicate RGB
entries, and channel bytes are preserved exactly. Because no active-count
field is established, all 256 register slots are imported. The result reports:

- omission of the 128 gradient slots;
- any `DRNG`, `CRNG`, or `BRNG` chunks not represented by `CustomPalette`;
- the absent active-register count;
- pre-AGA-compatible byte precision when every imported channel is a multiple
  of 17.

Malformed IFF, an unrecognized annotation, a wrong `CMAP` size, or an
unestablished chunk structure produces a controlled `PaletteCodecError`.
Nothing is silently repaired.

## Export and compatibility boundary

Export is intentionally unsupported. Although `CMAP` bytes can be generated,
doing so without an established contract for the gradient slots and range
chunks would create files that merely look plausible. No output has been
validated in Brilliance under emulation or by another independent Brilliance
writer/consumer. Consequently there is no channel quantization rule: import
retains the stored 8-bit bytes and export performs no conversion.

The codec is registered as binary, import-capable, and non-export-capable.
CLI and GUI import discovery share those flags; export selectors omit PLT.

```bash
retropal custom-palettes import palette.plt --format brilliance-plt
```

The imported register palette is saved through the ordinary native custom
palette store. Native persistence cannot retain Brilliance gradient slots or
range chunks; the import report states this loss. M2.4f validation and M2.5
colour-cycle editing remain separate planned work.
