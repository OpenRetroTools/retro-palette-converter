#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

# The workflow patcher was a one-time migration and is obsolete after this overlay.
rm -f scripts/patch-release-workflow-v012.py

uv lock

echo "Applied v0.1.2 release cleanup."
echo "Next: uv sync --python 3.12 --extra dev --extra gui --extra release"
