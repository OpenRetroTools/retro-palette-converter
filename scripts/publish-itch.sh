#!/usr/bin/env bash
set -euo pipefail

: "${ITCH_TARGET:?Set ITCH_TARGET, for example openretrotools/retro-palette-converter}"
command -v butler >/dev/null 2>&1 || {
  echo "butler is required: https://itch.io/docs/butler/" >&2
  exit 1
}

[[ -f dist/retro-palette-converter-linux-x86_64.zip ]] && \
  butler push dist/retro-palette-converter-linux-x86_64.zip "${ITCH_TARGET}:linux"
[[ -f dist/retro-palette-converter-windows-x86_64.zip ]] && \
  butler push dist/retro-palette-converter-windows-x86_64.zip "${ITCH_TARGET}:windows"

echo "Published available release archives to ${ITCH_TARGET}."
