# M2.3b — Changes

## Added

- `src/retropal/palettes/definitions/atari-2600-tia.json` — 128-colour TIA NTSC palette.
- `src/retropal/palettes/definitions/atari-8bit-antic-gtia.json` — 256-colour ANTIC/GTIA palette.
- `src/retropal/palettes/definitions/atari-st.json` — 16-colour Atari ST palette.
- `src/retropal/palettes/definitions/atari-ste.json` — 16-colour Atari STE palette.
- `src/retropal/palettes/definitions/atari-falcon030.json` — 256-colour Atari Falcon030 palette.
- `tests/test_atari_palettes.py` — registry presence, metadata completeness,
  color counts, unique IDs, RGB validity, family filtering, GUI
  discoverability (via `PALETTE_IDS`), and historical-accuracy caveat
  presence tests for all five new palettes.

## Modified

- `src/retropal/__init__.py` — `__version__` bumped from `0.2.0.dev1` to
  `0.2.0.dev2` (single version source; read by `retropal --version`,
  Help → About, and `hatch` build metadata via `[tool.hatch.version]`).
- `src/retropal/cli.py` — added `--family` option to the `palettes`
  subcommand; filtering is applied identically in plain and `--verbose`
  output via the existing `list_by_family()` registry query.
- `src/retropal/palettes/fixed.py` — registered the 5 new palette ids in
  `fixed_palette_ids()`, which automatically makes them available via
  `PALETTE_IDS`, `retropal palettes`, `retropal convert --palette`,
  `retropal batch --palette`, and both GUI palette combo boxes.
- `tests/test_cli.py` — added `--family` smoke tests (plain, case-insensitive,
  and verbose).
- `README.md` — documented the five new palettes, the `--family` CLI flag,
  and the "Atari platform pack" historical-accuracy notes.
- `CHANGELOG.md` — added the `### M2.3b` entry under `## Unreleased`,
  following the same structure as the existing `### M2.3a` entry.

## Not modified

- No adaptive-palette code (`palettes/amiga.py`, `palettes/amiga_ocs.py`)
  was touched; all five Atari palettes are fixed (non-adaptive), consistent
  with `PaletteInfo.adaptive = False` (the dataclass default).
- No GUI source files were modified. The GUI's palette combo boxes
  (`gui/main_window.py`, `gui/batch_dialog.py`) already populate themselves
  from `retropal.palettes.PALETTE_IDS`, so the new palettes appear there
  automatically once registered in `fixed_palette_ids()`.
- `pyproject.toml` was not modified: `dynamic = ["version"]` together with
  `[tool.hatch.version] path = "src/retropal/__init__.py"` already makes
  `__init__.py` the single version source; only that file needed editing.
