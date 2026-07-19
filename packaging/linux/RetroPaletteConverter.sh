#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

is_crostini() {
    [[ -e /dev/.cros_milestone ]] && return 0
    [[ -n "${SOMMELIER_VERSION:-}" ]] && return 0
    [[ -n "${CROS_USER_ID_HASH:-}" ]] && return 0
    [[ -n "${CHROMEOS_RELEASE_NAME:-}" ]] && return 0
    return 1
}

# Sommelier's Wayland integration can disconnect long-running Qt applications.
# Select XCB only for Crostini and never override an explicit user selection.
if is_crostini && [[ -z "${QT_QPA_PLATFORM+x}" ]]; then
    export QT_QPA_PLATFORM=xcb
fi

exec "$APP_DIR/RetroPaletteConverter" "$@"
