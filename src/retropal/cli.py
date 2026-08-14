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
from retropal.palettes.base import RGBColor
from retropal.palettes.custom import CustomPaletteError
from retropal.palettes.indexed import INDEXED_IMAGE_FORMATS, extract_indexed_palette
from retropal.palettes.interchange import (
    PaletteCodecError,
    export_palette,
    import_palette,
    iter_codecs,
)
from retropal.palettes.native import NativePaletteError, load_native_palette
from retropal.palettes.store import CustomPaletteStore, default_custom_palette_directory


def _rgb(value: str) -> RGBColor:
    """Parse #RRGGBB for conservative command-line palette editing."""
    text = value.removeprefix("#")
    if len(text) != 6:
        raise argparse.ArgumentTypeError("RGB colours must use #RRGGBB")
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("RGB colours must use #RRGGBB") from exc


def _add_conversion_palette_options(parser: argparse.ArgumentParser) -> None:
    choices = parser.add_mutually_exclusive_group(required=True)
    choices.add_argument("--palette", choices=PALETTE_IDS)
    choices.add_argument(
        "--custom-palette",
        type=Path,
        metavar="FILE",
        help="Use a native .retropal-palette.json file.",
    )


def _selected_palette(args: argparse.Namespace) -> tuple[str, tuple[RGBColor, ...] | None]:
    if args.custom_palette is None:
        return str(args.palette), None
    palette = load_native_palette(args.custom_palette)
    return palette.id, palette.colors


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
    _add_conversion_palette_options(convert_parser)
    convert_parser.add_argument(
        "--dither",
        choices=DITHER_IDS,
        default=DitherMode.NONE.value,
    )

    batch_parser = commands.add_parser("batch", help="Convert a directory of images.")
    batch_parser.add_argument("input", type=Path)
    batch_parser.add_argument("output", type=Path)
    _add_conversion_palette_options(batch_parser)
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

    custom_parser = commands.add_parser("custom-palettes", help="Manage native custom palettes.")
    custom_parser.add_argument(
        "--store", type=Path, default=default_custom_palette_directory(), help="Palette directory."
    )
    custom_commands = custom_parser.add_subparsers(dest="custom_command", required=True)
    custom_commands.add_parser("list", help="List stored custom palettes.")
    show = custom_commands.add_parser("show", help="Show one custom palette.")
    show.add_argument("id")
    create = custom_commands.add_parser("create", help="Create and save a custom palette.")
    create.add_argument("id")
    create.add_argument("name")
    create.add_argument("colors", type=_rgb, nargs="+")
    create.add_argument("--description", default="")
    create.add_argument("--source")
    rename = custom_commands.add_parser("rename", help="Rename a custom palette.")
    rename.add_argument("id")
    rename.add_argument("name")
    add = custom_commands.add_parser("add", help="Append a colour.")
    add.add_argument("id")
    add.add_argument("color", type=_rgb)
    set_color = custom_commands.add_parser("set", help="Replace a colour by index.")
    set_color.add_argument("id")
    set_color.add_argument("index", type=int)
    set_color.add_argument("color", type=_rgb)
    remove = custom_commands.add_parser("remove", help="Remove a colour by index.")
    remove.add_argument("id")
    remove.add_argument("index", type=int)
    move = custom_commands.add_parser("move", help="Move a colour to another index.")
    move.add_argument("id")
    move.add_argument("source_index", type=int)
    move.add_argument("target_index", type=int)
    delete = custom_commands.add_parser("delete", help="Delete a stored custom palette.")
    delete.add_argument("id")
    load = custom_commands.add_parser("load", help="Load a native file into the store.")
    load.add_argument("file", type=Path)
    interchange_import = custom_commands.add_parser(
        "import", help="Import an external palette into the native store."
    )
    interchange_import.add_argument("file", type=Path)
    interchange_import.add_argument(
        "--format", choices=tuple(codec.info.id for codec in iter_codecs())
    )
    image_import = custom_commands.add_parser(
        "import-image", help="Extract the stored palette from an indexed PNG, GIF, or BMP."
    )
    image_import.add_argument("file", type=Path)
    image_import.add_argument("--format", choices=INDEXED_IMAGE_FORMATS)
    image_import.add_argument("--id", dest="palette_id")
    image_import.add_argument("--name")
    interchange_export = custom_commands.add_parser(
        "export", help="Export a custom palette to an interchange format."
    )
    interchange_export.add_argument("id")
    interchange_export.add_argument(
        "--format", required=True, choices=tuple(codec.info.id for codec in iter_codecs())
    )
    interchange_export.add_argument("--output", "-o", required=True, type=Path)
    interchange_export.add_argument("--overwrite", action="store_true")
    return parser


def _custom_palette_command(args: argparse.Namespace) -> int:
    store = CustomPaletteStore(args.store)
    store.load_all()
    command = args.custom_command
    if command == "list":
        for palette in store.list():
            print(f"{palette.id}: {palette.name} ({len(palette.colors)} colours, custom)")
        return 0
    if command == "load":
        palette = store.load(args.file)
        path = store.save(palette.id)
        print(f"Loaded custom palette {palette.id} into {path}")
        return 0
    if command == "import":
        result = import_palette(args.file, format_id=args.format)
        palette = store.add(result.palette)
        path = store.save(palette.id)
        print(f"Imported {palette.id} as custom palette into {path}")
        _print_interchange_report(result.report.messages)
        return 0
    if command == "import-image":
        result = extract_indexed_palette(
            args.file,
            format_id=args.format,
            palette_id=args.palette_id,
            name=args.name,
        )
        palette = store.add(result.palette)
        path = store.save(palette.id)
        print(
            f"Extracted {result.stored_entry_count} stored {result.source_format.upper()} entries"
        )
        print(
            f"Image: {result.width}x{result.height}; used={len(result.used_indexes)}; "
            f"unused={len(result.unused_indexes)}"
        )
        if result.highest_used_index is not None:
            print(f"Highest referenced index: {result.highest_used_index}")
        if result.transparency is not None:
            indexes = ", ".join(map(str, result.transparency.non_opaque_indexes)) or "none"
            print(f"Non-opaque palette indexes: {indexes}")
        for message in result.messages:
            print(f"Warning: {message}")
        print(f"Saved custom palette {palette.id} to {path}")
        return 0
    if command == "export":
        palette = store.get(args.id)
        result = export_palette(
            palette,
            args.output,
            format_id=args.format,
            overwrite=args.overwrite,
        )
        print(f"Exported custom palette {palette.id} to {args.output}")
        _print_interchange_report(result.report.messages)
        return 0
    if command == "show":
        palette = store.get(args.id)
        print(f"{palette.id}: {palette.name} (custom)")
        if palette.description:
            print(f"Description: {palette.description}")
        if palette.source:
            print(f"Source: {palette.source}")
        for index, color in enumerate(palette.colors):
            print(f"{index}: #{color[0]:02X}{color[1]:02X}{color[2]:02X}")
        return 0
    if command == "create":
        palette = store.create(
            args.id,
            args.name,
            tuple(args.colors),
            description=args.description,
            source=args.source,
        )
    else:
        palette = store.get(args.id)
        if command == "rename":
            palette = palette.rename(args.name)
        elif command == "add":
            palette = palette.add_color(args.color)
        elif command == "set":
            palette = palette.set_color(args.index, args.color)
        elif command == "remove":
            palette = palette.remove_color(args.index)
        elif command == "move":
            palette = palette.move_color(args.source_index, args.target_index)
        elif command == "delete":
            store.delete(args.id)
            print(f"Deleted custom palette {args.id}")
            return 0
        else:
            raise CustomPaletteError(f"Unknown custom palette command: {command}")
        store.replace(palette)
    path = store.save(palette.id)
    print(f"Saved custom palette {palette.id} to {path}")
    return 0


def _print_interchange_report(messages: tuple[str, ...]) -> None:
    if not messages:
        print("Interchange report: lossless")
        return
    print("Interchange report:")
    for message in messages:
        print(f"  Warning: {message}")


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
        try:
            palette_id, colors = _selected_palette(args)
            convert_file(args.input, args.output, palette_id, args.dither, colors=colors)
        except (OSError, CustomPaletteError) as exc:
            parser.error(str(exc))
        print(f"Wrote {args.output}")
        return 0
    if args.command == "batch":
        try:
            palette_id, colors = _selected_palette(args)
        except (OSError, CustomPaletteError) as exc:
            parser.error(str(exc))
        result = convert_batch(
            args.input,
            args.output,
            palette_id,
            args.dither,
            recursive=args.recursive,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            colors=colors,
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
    if args.command == "custom-palettes":
        try:
            return _custom_palette_command(args)
        except (OSError, CustomPaletteError, NativePaletteError, PaletteCodecError) as exc:
            parser.error(str(exc))
    parser.error(f"Unknown command: {args.command}")
    return 2
