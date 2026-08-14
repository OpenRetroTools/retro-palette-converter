# Standard palette interchange

M2.4b maps every supported external format directly to and from the immutable
`CustomPalette` model. Codecs do not convert through the native persistence
document or through another interchange codec. Colour indexes and duplicate
RGB entries remain in their original order.

## Formats and capabilities

| Codec ID | Format | Extensions | Supported variant | Preserved model metadata |
| --- | --- | --- | --- | --- |
| `gpl` | GIMP GPL | `.gpl` | `GIMP Palette` header, UTF-8, name and RGB rows | name, colours |
| `jasc` | JASC-PAL | `.pal` | version `0100` | colours |
| `riff-pal` | Microsoft RIFF PAL | `.pal` | simple RGB `PAL ` form with `data`/`LOGPALETTE` | colours |
| `act` | Adobe Color Table | `.act` | 768-byte table and 772-byte table/count trailer | colours |
| `json` | RetroPal JSON interchange | `.json` | schema version 1 | ID, name, colours, description, source |
| `csv` | CSV palette | `.csv` | UTF-8 `index,r,g,b` rows | colours |
| `brilliance-plt` | Brilliance palette | `.plt` | verified Brilliance 1.0/2.0 `FORM ILBM` variant; import only | first 256 register colours |

All formats preserve RGB values, order, and duplicates within their supported
colour-count limits. Export reports identify every populated `CustomPalette`
field the target cannot represent. GPL per-colour labels, RIFF
`PALETTEENTRY` flags, and ACT transparency indexes have no generic model field;
imports report when those values are encountered rather than silently treating
them as RGB metadata.

The `.pal` extension is intentionally ambiguous. Imports distinguish JASC-PAL
and RIFF PAL by signature. Exports require explicit selection. Signatureless
ACT data is identified only with `.act` or an explicit format choice.

## Binary format basis

### Microsoft RIFF PAL

The implementation follows Microsoft's *Multimedia Programming Interface and
Data Specifications 1.0*, “Palette File Format”: the simple form is
`RIFF('PAL ' data(<palette:LOGPALETTE>))`; `LOGPALETTE` contains two 16-bit
fields followed by ordered four-byte `PALETTEENTRY` records (`red`, `green`,
`blue`, flags). It also follows Microsoft's RIFF chunk rules: 32-bit sizes are
little-endian, the top-level size excludes the first eight bytes, chunk sizes
exclude headers/padding, and chunks are word-aligned.

- [Microsoft Multimedia Programming Interface and Data Specifications 1.0](https://www.robotplanet.dk/audio/wav_meta_data/riff_mci.pdf), pp. 49–53.
- [Microsoft RIFF chunk structure](https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-).

Only the simple RGB form is written. Extended `plth`, YUV, and XYZ palettes are
not supported. Imported non-zero usage flags are reported and omitted; exports
write zero flags. Declared RIFF/chunk sizes and entry counts are checked before
accessing data.

### Adobe ACT

The implementation follows Adobe's *Photoshop File Formats Specification*,
“Additional File Formats → Color Table.” ACT has no signature or version: it
is exactly 768 or 772 bytes, with 256 consecutive RGB triples starting at
index zero. The optional four bytes are a two-byte used-colour count and a
two-byte transparency index. Adobe specifies high-order-byte-first ordering
for multi-byte Photoshop load-file values, so both trailer fields are decoded
and written big-endian.

- [Adobe Photoshop File Formats Specification](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/), “Color Table” and “Additional File Formats” byte-order notes.

For fewer than 256 colours, export zero-pads the RGB table and writes the
772-byte form with the exact count and `0xFFFF` (no transparency index). A
768-byte import necessarily represents all 256 entries because that form has
no count. Transparency is validated and reported but not mapped into the
RGB-only core model. More than 256 colours is a controlled export error.

## JSON formats

JSON interchange uses schema `org.openretrotools.palette-interchange`, version
1. It is not the application-native
`org.openretrotools.retropal.custom-palette` document and is discovered only
when its own schema matches. Native files remain the canonical per-user store;
interchange JSON is a portable external representation.

## CLI

```bash
retropal custom-palettes import palette.gpl
retropal custom-palettes import palette.pal --format riff-pal
retropal custom-palettes export my-palette --format jasc --output palette.pal
retropal custom-palettes export my-palette --format json --output palette.json
```

Imports are saved as normal native custom palettes. Exports refuse to overwrite
existing files unless `--overwrite` is supplied. Both commands print a
lossless result or explicit metadata warnings.

The GUI exposes the same registry through **Import…** and **Export…** in the
custom palette dialog and displays metadata-loss reports. Capability flags are
respected: import-only codecs are not offered for export.

Indexed-image extraction is documented in
[`indexed-image-palettes.md`](indexed-image-palettes.md). IFF/ILBM
`CMAP`/`CRNG` uses a separate container-preserving layer documented in
[`amiga-palette-interchange.md`](amiga-palette-interchange.md), rather than a
standard palette codec. Conservative Brilliance import is documented in
[`brilliance-plt.md`](brilliance-plt.md); its export contract and the broad
M2.4f conversion/validation engine remain planned.
