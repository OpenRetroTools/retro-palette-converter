#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest

echo
echo "Dither registry smoke test:"
uv run python - <<'PY'
from retropal.core.dither import list_dithers
print(", ".join(list_dithers()))
assert list_dithers() == (
    "none",
    "floyd-steinberg",
    "atkinson",
    "bayer-2x2",
    "bayer-4x4",
    "bayer-8x8",
)
PY

echo
echo "CLI smoke test:"
uv run retropal convert --help | grep -E "atkinson|bayer-2x2|bayer-4x4|bayer-8x8"
