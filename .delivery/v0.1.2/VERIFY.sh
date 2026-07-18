#!/usr/bin/env bash
set -euo pipefail

grep -q 'version = "0.1.2"' pyproject.toml
grep -q '^## 0.1.2' CHANGELOG.md
grep -q 'archive.with_name' scripts/add_linux_launcher_to_release.py
grep -q 'QT_QPA_PLATFORM=xcb' scripts/add_linux_launcher_to_release.py
test ! -e scripts/patch-release-workflow-v012.py

echo "Static v0.1.2 checks passed."
