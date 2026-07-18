#!/usr/bin/env bash
set -euo pipefail

: "${ITCH_TARGET:?Set ITCH_TARGET, for example account/retro-palette-converter}"

echo "itch.io publishing will be enabled when packaged builds exist in M3."
echo "Target: ${ITCH_TARGET}"
