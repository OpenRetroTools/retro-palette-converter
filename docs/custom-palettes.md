# Custom palettes

Custom palettes are user-owned, ordered RGB palettes. They are distinct from
the deterministic repository-owned hardware definitions in
`retropal.palettes.definitions`: creating or importing a custom palette never
changes the built-in registry or a platform profile.

Palette order is semantic. The core does not sort or deduplicate entries, and
the same RGB value may intentionally occur at several indexes. Custom palettes
must have a lowercase, hyphen-separated stable ID, a non-empty display name,
and at least one RGB colour whose channels are integers from 0 through 255.
Description and format-independent source/provenance text are optional.

## Native persistence

M2.4a stores one palette per `*.retropal-palette.json` file using schema
`org.openretrotools.retropal.custom-palette`, version 1. The document preserves
the ID, name, exact colour sequence (including duplicates), description, and
source. Unsupported versions, unknown/missing fields, and invalid values are
rejected rather than repaired.

This is Retro Palette Converter's versioned application-native persistence,
not the general JSON interchange format planned for M2.4b. Native documents
are intentionally namespaced and use a distinctive filename suffix.

The default user directory is:

- Linux: `$XDG_DATA_HOME/retropal/palettes`, or
  `~/.local/share/retropal/palettes` when `XDG_DATA_HOME` is unset;
- macOS: `~/Library/Application Support/RetroPaletteConverter/palettes`;
- Windows: `%APPDATA%\OpenRetroTools\RetroPaletteConverter\palettes`.

Set `RETROPAL_PALETTE_DIR` to override it. CLI commands also accept
`custom-palettes --store DIRECTORY` for an explicit store.

## CLI workflow

```bash
retropal custom-palettes create sunset "Sunset" '#101020' '#E05040' '#101020'
retropal custom-palettes rename sunset "Sunset Study"
retropal custom-palettes add sunset '#FFD080'
retropal custom-palettes set sunset 1 '#D04030'
retropal custom-palettes move sunset 3 1
retropal custom-palettes remove sunset 2
retropal custom-palettes list
retropal custom-palettes show sunset
retropal convert input.png \
  --custom-palette ~/.local/share/retropal/palettes/sunset.retropal-palette.json \
  --dither bayer-4x4 --output output.png
```

`load FILE` copies a valid native document into the selected store; `delete ID`
removes the stored native document. Built-in conversion continues to use
`--palette BUILTIN_ID`.

## GUI workflow

Open **Tools → Custom Palettes…**. The editor can create and rename palettes,
add/edit/remove colours, move entries up or down, save or reopen native files,
delete palettes, and select a custom palette for conversion. Editing delegates
to the same Qt-independent immutable model and store used by the CLI.

Standard GPL, JASC-PAL, RIFF PAL, ACT, JSON, and CSV interchange is documented
in [`palette-interchange.md`](palette-interchange.md). Stored-palette extraction
from indexed PNG, GIF, and BMP is documented in
[`indexed-image-palettes.md`](indexed-image-palettes.md). Brilliance PLT and
broad cross-format validation remain M2.4e–f work.

Amiga IFF/ILBM CMAP workflows and their separate container/CRNG state are
documented in
[`amiga-palette-interchange.md`](amiga-palette-interchange.md). Native palette
files retain imported RGB entries but not ILBM-specific metadata.
