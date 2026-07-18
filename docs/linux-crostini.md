# Linux and ChromeOS/Crostini

Retro Palette Converter normally lets Qt select the native Linux display
backend.

ChromeOS Linux development environments use a Wayland bridge that can
occasionally disconnect Qt applications. The Linux release therefore includes
a launcher named:

```text
RetroPaletteConverter.sh
```

The launcher:

- respects an existing `QT_QPA_PLATFORM` setting;
- detects ChromeOS/Crostini;
- selects `QT_QPA_PLATFORM=xcb` only under Crostini;
- leaves normal Linux systems unchanged.

## Starting on ChromeOS

```bash
chmod +x RetroPaletteConverter.sh
./RetroPaletteConverter.sh
```

Install the XCB runtime libraries if necessary:

```bash
sudo apt update
sudo apt install -y \
  libxcb-cursor0 \
  libxkbcommon-x11-0 \
  libxcb-xinerama0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```
