#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Run this from inside the retro-palette-converter Git repository." >&2
  exit 1
}
cd "$repo_root"

patch_file=".delivery/m2/0001-m2-minimal-qt-gui.patch"
if [[ ! -f "$patch_file" ]]; then
  echo "Missing $patch_file. Unpack the delivery ZIP into the repository root first." >&2
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "The repository has uncommitted changes. Commit or stash them before applying M2." >&2
  git status --short
  exit 1
fi

git apply --check "$patch_file"
git apply "$patch_file"
echo "M2 patch applied. Run .delivery/m2/VERIFY.sh next."
