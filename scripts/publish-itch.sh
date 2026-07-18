#!/usr/bin/env bash
set -euo pipefail

command -v butler >/dev/null 2>&1 || {
  echo "butler is required: https://itch.io/docs/butler/installing.html" >&2
  exit 1
}

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 ITCH_TARGET VERSION" >&2
  exit 2
fi

target="$1"
version="$2"

push_if_present() {
  local file="$1"
  local channel="$2"
  if [[ -f "$file" ]]; then
    butler push "$file" "$target:$channel" --userversion "$version"
  else
    echo "Skipping missing file: $file"
  fi
}

push_if_present dist/retro-palette-converter-windows-x86_64.zip windows
push_if_present dist/retro-palette-converter-linux-x86_64.zip linux
push_if_present dist/retro-palette-converter-macos-arm64.zip macos-apple-silicon
push_if_present dist/retro-palette-converter-macos-x86_64.zip macos-intel
