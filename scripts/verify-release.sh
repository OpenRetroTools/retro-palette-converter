#!/usr/bin/env bash
set -euo pipefail

uv sync --extra dev --extra gui
uv run ruff format --check .
uv run ruff check .
uv run pytest
uv run python -m compileall -q src
git diff --check

echo "Release source verification passed."
echo "Native binaries are built by .github/workflows/release.yml."
