"""Command-line interface for Retro Palette Converter."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from retropal import __version__
from retropal.core.converter import convert_file
from retropal.core.image_io import inspect_image
from retropal.core.models import DitherMode
from retropal.palettes import PALETTE_IDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="retropal",
        description="Convert images to retro color palettes.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Retro Palette Converter {__version__}",
    )
    commands = parser.add_subparsers(dest="command")

    convert_parser = commands.add_parser("convert", help="Convert a PNG image.")
    convert_parser.add_argument("input", type=Path)
    convert_parser.add_argument("--output", "-o", type=Path, required=True)
    convert_parser.add_argument("--palette", choices=PALETTE_IDS, required=True)
    convert_parser.add_argument(
        "--dither",
        choices=tuple(mode.value for mode in DitherMode),
        default=DitherMode.NONE.value,
    )

    commands.add_parser("palettes", help="List available palettes.")
    inspect_parser = commands.add_parser("inspect", help="Inspect a PNG image.")
    inspect_parser.add_argument("input", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "palettes":
        print("\n".join(PALETTE_IDS))
        return 0
    if args.command == "inspect":
        info = inspect_image(args.input)
        print(f"Image: {args.input}")
        print(f"Dimensions: {info.width}x{info.height}")
        print(f"Mode: {info.mode}")
        print(f"Unique RGB colors: {info.unique_rgb_colors}")
        print(f"Alpha: {'yes' if info.has_alpha else 'no'}")
        return 0
    if args.command == "convert":
        convert_file(args.input, args.output, args.palette, DitherMode(args.dither))
        print(f"Wrote {args.output}")
        return 0
    parser.error(f"Unknown command: {args.command}")
    return 2
