# Indexed-image palette import

M2.4c extracts the stored colour table from indexed PNG, GIF, and BMP images
directly into the immutable `CustomPalette` model. This is intentionally
different from extracting or quantizing colours from a true-colour image.

The complete stored table is semantic: unused entries, duplicate RGB values,
and index order are preserved. Pixel usage is reported separately and never
prunes the palette.

## Supported structures

| Format | Stored structure | Transparency | Pixel usage |
| --- | --- | --- | --- |
| indexed PNG | `PLTE`, 1/2/4/8-bit index depth | `tRNS` expanded by index; omitted entries are opaque | Pillow decodes indexes |
| GIF87a/GIF89a | first frame's effective global or local colour table | Graphic Control Extension transparent index | Pillow decodes frame 0 indexes |
| BMP | uncompressed 1/4/8-bit `BITMAPCOREHEADER` and Windows 40/52/56/108/124-byte DIBs | none; BI_RGB reserved bytes are not alpha | narrow raw packed-pixel reader |

PNG and GIF container structures are parsed directly so Pillow cannot
normalize the stored table and related metadata. Pillow is used narrowly to
decode pixel indexes for informational usage statistics. BMP palette tables
and uncompressed packed indexes are both read directly with explicit
little-endian fields and bounds checks.

Compressed BMP variants and non-indexed images are rejected. This milestone
does not perform general true-colour extraction or median-cut generation.

## Transparency and GIF frames

Transparency remains extraction metadata: alpha values keyed by palette index.
`CustomPalette` remains RGB-only. PNG partial `tRNS` tables are completed with
opaque (`255`) values. A GIF transparent index becomes alpha 0 for that index
and 255 for the other entries.

Native custom-palette persistence currently stores RGB palette identity, not
this transparency report. CLI and GUI imports explicitly warn when non-opaque
metadata therefore will not survive native save.

For GIF, extraction deterministically uses the first image frame and its local
colour table when present, otherwise its global table. The result reports the
frame count. Multi-frame files produce a policy warning; if later frames have
different effective tables, that limitation is reported and the result is not
marked as preserving every stored palette semantic across the whole file.

## CLI and GUI

```bash
retropal custom-palettes import-image artwork.png
retropal custom-palettes import-image animation.gif --id title-cycle --name "Title Cycle"
retropal custom-palettes import-image icon.bmp --format bmp
```

Signature detection distinguishes PNG, GIF, and BMP. `--format` must agree
with the signature. IDs derive deterministically from the filename unless
overridden; existing IDs are never silently replaced. Successful imports are
saved as normal native custom palettes and can immediately be selected for
conversion.

In the desktop editor, use **Tools → Custom Palettes… → Import Image…**. The
summary shows stored, used, and unused entry counts plus transparency and GIF
limitations. The imported palette can then be edited, saved, or selected like
any other custom palette.

IFF/ILBM and CMAP/CRNG are handled by the separate metadata-preserving workflow
in [`amiga-palette-interchange.md`](amiga-palette-interchange.md). Brilliance
PLT import is documented in [`brilliance-plt.md`](brilliance-plt.md); its
unverified export contract and general palette conversion/validation (M2.4f)
remain planned.
