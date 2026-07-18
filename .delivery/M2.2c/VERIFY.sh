#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q

echo
echo "Dither registry smoke test:"
uv run python - <<'PY'
from retropal.core.dither import list_dithers

print(", ".join(list_dithers()))
PY

echo
echo "CLI smoke test:"
uv run retropal convert --help | grep -- "--dither"
