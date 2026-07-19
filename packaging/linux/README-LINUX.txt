Retro Palette Converter for Linux
==================================

Start the application through the launcher:

    ./RetroPaletteConverter.sh

On ordinary Linux desktops the launcher lets Qt select its normal display
backend. Under ChromeOS/Crostini it selects the more reliable XCB backend,
unless QT_QPA_PLATFORM is already set by the user.

ChromeOS / Crostini
-------------------

If the launcher is not executable after extraction:

    chmod +x RetroPaletteConverter.sh

If automatic Crostini detection is unavailable, use this direct fallback:

    QT_QPA_PLATFORM=xcb ./RetroPaletteConverter

Required Crostini packages when XCB libraries are missing:

    sudo apt update
    sudo apt install -y \
      libxcb-cursor0 \
      libxkbcommon-x11-0 \
      libxcb-xinerama0 \
      libxcb-icccm4 \
      libxcb-image0 \
      libxcb-keysyms1 \
      libxcb-render-util0
