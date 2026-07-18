#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" || "$PWD" != "$repo_root" ]]; then
  echo "Run this from the root of the retro-palette-converter Git repository." >&2
  exit 1
fi

patch_file=".delivery/m3/0001-m3-refine-gui.patch"
if git apply --reverse --check "$patch_file" >/dev/null 2>&1; then
  echo "M3 patch is already applied."
  exit 0
fi

git apply --check "$patch_file"
git apply "$patch_file"
echo "M3 patch applied. Run .delivery/m3/VERIFY.sh next."
