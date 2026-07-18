#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
echo "M2.1b files are applied by extracting the overlay into the repository root."
echo "Run ./.delivery/M2.1b/VERIFY.sh"
