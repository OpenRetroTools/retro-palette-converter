#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

if [[ -f src/retropal/core/dithering.py ]]; then
  echo "ERROR: legacy src/retropal/core/dithering.py still exists; run APPLY.sh" >&2
  exit 1
fi

uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest

echo
echo "Dither registry smoke test:"
uv run python - <<'PY'
from retropal.core.dither import DITHER_IDS, iter_dithers

print(", ".join(DITHER_IDS))
assert tuple(item.id for item in iter_dithers()) == DITHER_IDS
PY

echo
echo "GUI import smoke test:"
QT_QPA_PLATFORM=offscreen uv run python - <<'PY'
from retropal.gui.batch_dialog import BatchConvertDialog
from retropal.gui.main_window import MainWindow

print(BatchConvertDialog.__name__, MainWindow.__name__)
PY
