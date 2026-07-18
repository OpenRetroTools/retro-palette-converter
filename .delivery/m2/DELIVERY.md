# Retro Palette Converter — M2 delivery

## Contents

- Minimal PySide6 desktop GUI.
- Open PNG through the file chooser.
- Drop a PNG onto the original preview.
- Original and converted side-by-side previews.
- Live palette and dithering selection.
- PNG export with a suggested filename.
- `retropal gui` and `retropal-gui` launch commands.
- PySide6 remains optional for CLI-only installations.
- Two additional tests; expected total: 24.

## Apply

From the repository root:

```bash
unzip -o ~/Downloads/retro-palette-converter-m2-patch.zip -d .
./.delivery/m2/APPLY.sh
./.delivery/m2/VERIFY.sh
```

Then test the interface:

```bash
uv run retropal gui
```

Open or drop `examples/gradient.png`, change palette/dithering, and export a PNG.

## Commit

After successful verification:

```bash
git add .
git commit -m "M2: Add minimal Qt GUI"
```

The `.delivery/` directory may be deleted before committing if delivery metadata should not
be retained in the repository.
