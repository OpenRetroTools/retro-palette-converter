#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
uv run python -m compileall -q src

echo
echo "GUI import smoke test:"
uv run python -c 'from retropal.gui.batch_dialog import BatchConvertDialog; print(BatchConvertDialog.__name__)'
