#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Run this from inside the retro-palette-converter Git repository." >&2
  exit 1
}
cd "$repo_root"

unset UV_INDEX_URL UV_DEFAULT_INDEX UV_EXTRA_INDEX_URL
unset PIP_INDEX_URL PIP_EXTRA_INDEX_URL

uv sync --extra dev --extra gui --default-index https://pypi.org/simple
uv run ruff format --check src tests
uv run ruff check .
uv run pytest
uv run retropal --version
uv run retropal --help

echo
echo "Verification passed. Start the GUI with: uv run retropal gui"
