# M3 — Refined GUI architecture

## Included

- Qt-independent `ConverterController`
- zoomable and pannable `QGraphicsView` previews
- Fit, 100%, zoom-in and zoom-out toolbar actions
- synchronized zoom actions for original and converted previews
- project-local XCB launcher for Linux and ChromeOS Crostini
- controller tests
- version bump to `0.4.0.dev0`

## Apply

```bash
unzip -o ~/Downloads/retro-palette-converter-m3-patch.zip -d .
./.delivery/m3/APPLY.sh
./.delivery/m3/VERIFY.sh
```

## Run on ChromeOS/Crostini

```bash
./scripts/run-gui-linux.sh
```

## Expected verification

- Ruff formatting: clean
- Ruff lint: clean
- Tests: 26 passed
- Version: Retro Palette Converter 0.4.0.dev0
