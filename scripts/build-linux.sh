#!/usr/bin/env bash
set -euo pipefail

echo "Local builds are for development diagnostics only."
echo "Official packages are built by GitHub Actions."
exec uv run --with pyinstaller python scripts/build_release.py
