#!/usr/bin/env python3
"""Verify that fixed-palette resources exist in a packaged application."""

from __future__ import annotations

import argparse
from pathlib import Path

from retropal.palettes.fixed import fixed_palette_ids


def verify_bundle(bundle: Path) -> None:
    definitions = bundle / "_internal/retropal/palettes/definitions"
    missing = [
        palette_id
        for palette_id in fixed_palette_ids()
        if not (definitions / f"{palette_id}.json").is_file()
    ]
    if missing:
        raise RuntimeError(
            f"Packaged fixed-palette definitions are missing from {definitions}: "
            + ", ".join(missing)
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bundle",
        nargs="?",
        type=Path,
        default=Path("dist/RetroPaletteConverter"),
    )
    args = parser.parse_args()
    verify_bundle(args.bundle)
    print(f"Verified packaged fixed-palette definitions in {args.bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
