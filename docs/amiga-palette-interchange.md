# Amiga IFF/ILBM palette interchange

M2.4d provides a narrow metadata-preserving ILBM document layer. It is
separate from the standard palette codec registry because ILBM is an image
container whose `BODY`, colour-cycle data, annotations, and unknown chunks
must survive a palette-only update. `CustomPalette` remains the canonical
ordered RGB model; raw IFF state lives only in `IlbmDocument`.

## Format basis

The implementation follows these historical specifications and maintained
copies of the original material:

- Electronic Arts, [“EA IFF 85” Standard for Interchange Format Files](https://wiki.amigaos.net/wiki/EA_IFF_85_Standard_for_Interchange_Format_Files).
- Commodore-Amiga, [ILBM IFF Interleaved Bitmap](https://wiki.amigaos.net/wiki/ILBM_IFF_Interleaved_Bitmap), including the 1988 registry additions for CRNG flags.
- Commodore, [ILBM regular-expression summary](https://amigadev.elowar.com/read/ADCD_2.1/Devices_Manual_guide/node01BB.html).

IFF uses four-byte identifiers and unsigned big-endian 32-bit chunk sizes.
`FORM` size counts its four-byte form type and contained chunks, but excludes
the outer `FORM` ID and size. An odd-sized chunk has one alignment byte that is
not included in its declared size. The parser bounds-checks all declared sizes
and retains the original alignment byte, including its value.

## Supported subset

The parser accepts one complete top-level `FORM ILBM`. It records every child
chunk in order with its exact payload and pad byte. It does not decode `BMHD`,
`BODY`, bitplanes, compression, HAM, or EHB display semantics.

`CMAP` is zero or more RGB triples, ordered by colour-register index. For
import into the non-empty `CustomPalette` model, the effective CMAP must contain
at least one complete triple. Values, order, duplicates, and short palette
tables are retained exactly; entries are never padded or pruned.

The ILBM property rule says that when a property repeats, its last occurrence
before `BODY` is effective. Accordingly, multiple CMAP chunks are preserved,
reported, and the last one is imported or replaced. A newly added CMAP is
inserted immediately before `BODY`, or at the end when BODY is absent. CMAP or
CRNG after BODY is conservatively rejected.

## CRNG

Each CRNG must contain the documented eight-byte big-endian `CRange` record:

```text
reserved: UWORD
rate:     UWORD
flags:    UWORD
low:      UBYTE
high:     UBYTE
```

All ranges remain ordered. The typed view exposes the raw values and payload,
plus direct flag interpretations: bit 0 (`RNG_ACTIVE`) means enabled and bit 1
(`RNG_REVERSE`) means reverse. Other bits and the reserved word are retained
without interpretation. Rate units use 16384 for 60 steps/second.

Historical documentation warns that some Deluxe Paint output sets ACTIVE but
uses rate 36 to mean inactive. RetroPal reports the stored bit and rate rather
than guessing around this ambiguity. M2.4d does not edit or animate CRNG.

## Preservation and metadata boundaries

Replacing CMAP rebuilds only the FORM/chunk length framing and the selected
CMAP. Original order and every non-CMAP chunk object are retained, including
CRNG, `BODY`, `ANNO`, `AUTH`, and unknown IDs. Their payloads and original pad
bytes therefore remain byte-for-byte identical. Earlier CMAP chunks also remain
unchanged when the effective last CMAP is replaced.

Importing CMAP into native `*.retropal-palette.json` preserves its RGB identity
but cannot store CRNG, unknown chunks, BODY, padding, or container order. CLI
and GUI imports explicitly report that boundary. To preserve ILBM state, use
the ILBM replace/update workflow against the original document.

## CLI and GUI

```bash
retropal ilbm inspect picture.iff
retropal custom-palettes import-ilbm picture.iff --id title-palette
retropal ilbm --store PALETTE_DIRECTORY replace-palette picture.iff \
  --palette title-palette --output updated.iff
```

Writes refuse to replace an existing output unless `--overwrite` is supplied.
Inspection lists chunk order, CMAP entry count, and each CRNG range's raw rate,
flags, indexes, enabled bit, and direction bit.

The custom-palette dialog provides **Import ILBM…** and **Update ILBM…**.
Import displays CRNG summaries and native-persistence limitations. Update uses
the currently selected custom palette as CMAP and writes a separate ILBM while
preserving other chunks.

Brilliance PLT export and the M2.5 colour-cycle preview/editor remain
deliberately deferred.

M2.4f validation can carry an `ilbm-document-metadata-not-preserved` issue when
an extracted `CustomPalette` leaves this document-preserving workflow. CRNG,
BODY, and raw chunks remain in `IlbmDocument`, not `CustomPalette`.
