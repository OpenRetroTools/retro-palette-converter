#!/usr/bin/env python3
"""Verify that fixed-palette resources exist in a packaged application."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from retropal.palettes.fixed import _palette_from_payload, fixed_palette_ids


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
    for palette_id in fixed_palette_ids():
        path = definitions / f"{palette_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        palette = _palette_from_payload(payload, str(path))
        if palette.id != palette_id:
            raise RuntimeError(
                f"Packaged palette {path} contains ID {palette.id!r}, expected {palette_id!r}"
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
