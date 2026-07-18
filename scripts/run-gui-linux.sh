#!/usr/bin/env bash
set -euo pipefail

# Qt/Wayland can be unstable in some ChromeOS/Crostini environments.
export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
exec uv run retropal gui "$@"
