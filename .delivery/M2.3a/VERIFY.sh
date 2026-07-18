#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
uv run ruff check src tests
uv run ruff format --check src tests
uv run pytest
printf '\nPalette metadata smoke test:\n'
uv run retropal palettes --verbose | grep -E 'commodore-64:|vic-20:|commodore-plus4:|amiga-ecs-64:|amiga-aga-256:'
printf '\nVersion smoke test:\n'
uv run retropal --version
