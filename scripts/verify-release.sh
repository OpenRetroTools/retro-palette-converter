#!/usr/bin/env bash
set -euo pipefail
uv sync --extra dev --extra gui --default-index https://pypi.org/simple
uv run ruff format --check src tests
uv run ruff check .
uv run pytest
uv run python -m compileall -q src
uv run retropal --version
