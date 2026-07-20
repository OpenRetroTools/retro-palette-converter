#!/usr/bin/env python3
"""Generate the registered platform-profile palette inventory."""

from __future__ import annotations

import argparse
from pathlib import Path

from retropal.palettes.inventory import inventory_markdown


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", nargs="?", type=Path, default=Path("docs/palette-inventory.md"))
    args = parser.parse_args()
    args.output.write_text(inventory_markdown(), encoding="utf-8")
    print(f"Generated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
