#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest -q

echo
echo "Compare dialog smoke test:"
QT_QPA_PLATFORM=offscreen uv run python - <<'PY'
from retropal.gui.compare_dialog import DEFAULT_COMPARE_IDS, CompareDitheringDialog

print(CompareDitheringDialog.__name__)
print(", ".join(DEFAULT_COMPARE_IDS))
PY
