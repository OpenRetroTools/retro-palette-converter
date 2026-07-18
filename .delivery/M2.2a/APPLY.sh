#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# M2.2a replaces the old single-file module with the dither package.
rm -f src/retropal/core/dithering.py
find src tests -type d -name __pycache__ -prune -exec rm -rf {} +

echo "M2.2a dithering framework applied."
echo "Run ./.delivery/M2.2a/VERIFY.sh"
