"""Command-line interface for Retro Palette Converter."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from retropal import __version__
from retropal.core.batch import convert_batch
from retropal.core.converter import convert_file
from retropal.core.dither import DITHER_IDS
from retropal.core.image_io import inspect_image
from retropal.core.models import DitherMode
from retropal.palettes import PALETTE_IDS, iter_palette_info, list_by_family


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
        choices=DITHER_IDS,
        default=DitherMode.NONE.value,
    )

    batch_parser = commands.add_parser("batch", help="Convert a directory of images.")
    batch_parser.add_argument("input", type=Path)
    batch_parser.add_argument("output", type=Path)
    batch_parser.add_argument("--palette", choices=PALETTE_IDS, required=True)
    batch_parser.add_argument(
        "--dither",
        choices=DITHER_IDS,
        default=DitherMode.NONE.value,
    )
    batch_parser.add_argument(
        "--recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include subdirectories (default: enabled).",
    )
    batch_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing output files.",
    )
    batch_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be converted without writing files.",
    )

    palettes_parser = commands.add_parser("palettes", help="List available palettes.")
    palettes_parser.add_argument("--verbose", "-v", action="store_true")
    palettes_parser.add_argument(
        "--family",
        help="Only show palettes belonging to the given family (case-insensitive).",
    )
    commands.add_parser("gui", help="Start the desktop application.")
    inspect_parser = commands.add_parser("inspect", help="Inspect a PNG image.")
    inspect_parser.add_argument("input", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "gui":
        from retropal.application import run_gui

        return run_gui()
    if args.command == "palettes":
        infos = list_by_family(args.family) if args.family else iter_palette_info()
        if not args.verbose:
            print("\n".join(info.id for info in infos))
            return 0
        for info in infos:
            mode = "adaptive" if info.adaptive else "fixed"
            print(f"{info.id}: {info.name}")
            print(f"  Family: {info.family}")
            print(f"  Manufacturer: {info.manufacturer}")
            print(f"  Year: {info.year if info.year is not None else 'unknown'}")
            print(f"  Colours: {info.color_count} ({mode})")
            print(f"  {info.description}")
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
        convert_file(args.input, args.output, args.palette, args.dither)
        print(f"Wrote {args.output}")
        return 0
    if args.command == "batch":
        result = convert_batch(
            args.input,
            args.output,
            args.palette,
            args.dither,
            recursive=args.recursive,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )
        action = "Would write" if args.dry_run else "Wrote"
        for path in result.converted:
            print(f"{action} {path}")
        for path in result.skipped:
            print(f"Skipped existing {path}")
        for failure in result.failures:
            print(f"Failed {failure.source}: {failure.message}")
        print(
            "Summary: "
            f"converted={len(result.converted)} "
            f"skipped={len(result.skipped)} "
            f"failed={len(result.failures)}"
        )
        return 0 if result.success else 1
    parser.error(f"Unknown command: {args.command}")
    return 2
