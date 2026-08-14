"""Command-line interface for Retro Palette Converter."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path

from retropal import __version__
from retropal.core.batch import convert_batch
from retropal.core.converter import convert_file
from retropal.core.dither import DITHER_IDS
from retropal.core.image_io import inspect_image
from retropal.core.models import DitherMode
from retropal.palettes import PALETTE_IDS, iter_palette_info, list_by_family
from retropal.palettes.amiga_iff import (
    ColorCycleRange,
    IlbmDocument,
    IlbmPaletteError,
    add_ilbm_cycle,
    decode_indexed_ilbm,
    edit_ilbm_cycle,
    import_ilbm_palette,
    inspect_ilbm,
    palette_at,
    remove_ilbm_cycle,
    render_indexed_preview,
    replace_ilbm_palette,
    validate_cycles,
)
from retropal.palettes.base import RGBColor
from retropal.palettes.custom import CustomPaletteError
from retropal.palettes.indexed import INDEXED_IMAGE_FORMATS, extract_indexed_palette
from retropal.palettes.interchange import (
    PaletteCodecError,
    export_palette,
    import_palette,
    iter_codecs,
)
from retropal.palettes.interchange import (
    convert_palette as convert_interchange_palette,
)
from retropal.palettes.native import NativePaletteError, load_native_palette, save_native_palette
from retropal.palettes.store import CustomPaletteStore, default_custom_palette_directory
from retropal.palettes.validation import (
    ConversionPlan,
    ExecutionPolicy,
    PaletteAnalysis,
    PaletteValidationError,
    ValidationIssue,
    analyze_palette,
    execute_plan,
    get_hardware_target,
    plan_format_conversion,
    plan_hardware_conversion,
)


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
        "--format", choices=tuple(codec.info.id for codec in iter_codecs() if codec.info.can_import)
    )
    image_import = custom_commands.add_parser(
        "import-image", help="Extract the stored palette from an indexed PNG, GIF, or BMP."
    )
    image_import.add_argument("file", type=Path)
    image_import.add_argument("--format", choices=INDEXED_IMAGE_FORMATS)
    image_import.add_argument("--id", dest="palette_id")
    image_import.add_argument("--name")
    ilbm_import = custom_commands.add_parser(
        "import-ilbm", help="Import the effective CMAP from an Amiga ILBM."
    )
    ilbm_import.add_argument("file", type=Path)
    ilbm_import.add_argument("--id", dest="palette_id")
    ilbm_import.add_argument("--name")
    interchange_export = custom_commands.add_parser(
        "export", help="Export a custom palette to an interchange format."
    )
    interchange_export.add_argument("id")
    interchange_export.add_argument(
        "--format",
        required=True,
        choices=tuple(codec.info.id for codec in iter_codecs() if codec.info.can_export),
    )
    interchange_export.add_argument("--output", "-o", required=True, type=Path)
    interchange_export.add_argument("--overwrite", action="store_true")
    analysis = custom_commands.add_parser("analyze", help="Analyze palette statistics and indexes.")
    analysis.add_argument("id")
    analysis.add_argument("--json", action="store_true")
    plan = custom_commands.add_parser("plan", help="Plan conversion to an interchange format.")
    plan.add_argument("id")
    plan.add_argument(
        "--target-format", required=True, choices=tuple(c.info.id for c in iter_codecs())
    )
    plan.add_argument("--json", action="store_true")
    validate = custom_commands.add_parser(
        "validate", help="Validate against a hardware or fixed palette target."
    )
    validate.add_argument("id")
    validate.add_argument("--target", required=True)
    validate.add_argument("--json", action="store_true")
    palette_convert = custom_commands.add_parser(
        "convert", help="Plan and explicitly execute palette-format conversion."
    )
    palette_convert.add_argument("id")
    palette_convert.add_argument(
        "--target-format", required=True, choices=tuple(c.info.id for c in iter_codecs())
    )
    palette_convert.add_argument("--output", "-o", required=True, type=Path)
    palette_convert.add_argument("--overwrite", action="store_true")
    palette_convert.add_argument("--allow-metadata-loss", action="store_true")
    transform = custom_commands.add_parser(
        "transform", help="Explicitly transform for a hardware/fixed-palette target."
    )
    transform.add_argument("id")
    transform.add_argument("--target", required=True)
    transform.add_argument("--output", "-o", required=True, type=Path)
    transform.add_argument("--overwrite", action="store_true")
    transform.add_argument("--allow-channel-quantization", action="store_true")
    transform.add_argument("--allow-fixed-palette-remap", action="store_true")
    transform.add_argument("--allow-color-reduction", action="store_true")
    transform.add_argument("--allow-index-changes", action="store_true")

    ilbm_parser = commands.add_parser("ilbm", help="Inspect or update Amiga ILBM metadata.")
    ilbm_parser.add_argument(
        "--store", type=Path, default=default_custom_palette_directory(), help="Palette directory."
    )
    ilbm_commands = ilbm_parser.add_subparsers(dest="ilbm_command", required=True)
    ilbm_inspect = ilbm_commands.add_parser("inspect", help="Inspect ILBM chunks and CRNG ranges.")
    ilbm_inspect.add_argument("input", type=Path)
    ilbm_replace = ilbm_commands.add_parser(
        "replace-palette", help="Replace or add CMAP while preserving other chunks."
    )
    ilbm_replace.add_argument("input", type=Path)
    ilbm_replace.add_argument("--palette", required=True)
    ilbm_replace.add_argument("--output", "-o", required=True, type=Path)
    ilbm_replace.add_argument("--overwrite", action="store_true")
    ilbm_cycles = ilbm_commands.add_parser("cycles", help="Inspect CRNG colour-cycle ranges.")
    ilbm_cycles.add_argument("input", type=Path)
    ilbm_cycles.add_argument("--json", action="store_true")
    cycle_at = ilbm_commands.add_parser("cycle-at", help="Evaluate palette state at elapsed time.")
    cycle_at.add_argument("input", type=Path)
    cycle_at.add_argument("--time", required=True, type=Fraction)
    cycle_at.add_argument("--json", action="store_true")
    cycle_preview = ilbm_commands.add_parser(
        "cycle-preview", help="Render an indexed ILBM at an elapsed time."
    )
    cycle_preview.add_argument("input", type=Path)
    cycle_preview.add_argument("--time", required=True, type=Fraction)
    cycle_preview.add_argument("--output", "-o", required=True, type=Path)
    cycle_preview.add_argument("--overwrite", action="store_true")
    cycle_add = ilbm_commands.add_parser("cycle-add", help="Add a CRNG range to a new ILBM.")
    cycle_add.add_argument("input", type=Path)
    cycle_add.add_argument("--output", "-o", required=True, type=Path)
    cycle_add.add_argument("--rate", required=True, type=int)
    cycle_add.add_argument("--low", required=True, type=int)
    cycle_add.add_argument("--high", required=True, type=int)
    cycle_add.add_argument("--active", action=argparse.BooleanOptionalAction, default=True)
    cycle_add.add_argument("--reverse", action=argparse.BooleanOptionalAction, default=False)
    cycle_add.add_argument("--overwrite", action="store_true")
    cycle_set = ilbm_commands.add_parser("cycle-set", help="Edit one CRNG range in a new ILBM.")
    cycle_set.add_argument("input", type=Path)
    cycle_set.add_argument("index", type=int)
    cycle_set.add_argument("--output", "-o", required=True, type=Path)
    cycle_set.add_argument("--rate", type=int)
    cycle_set.add_argument("--low", type=int)
    cycle_set.add_argument("--high", type=int)
    cycle_set.add_argument("--active", action=argparse.BooleanOptionalAction)
    cycle_set.add_argument("--reverse", action=argparse.BooleanOptionalAction)
    cycle_set.add_argument("--overwrite", action="store_true")
    cycle_remove = ilbm_commands.add_parser(
        "cycle-remove", help="Remove one CRNG range in a new ILBM."
    )
    cycle_remove.add_argument("input", type=Path)
    cycle_remove.add_argument("index", type=int)
    cycle_remove.add_argument("--output", "-o", required=True, type=Path)
    cycle_remove.add_argument("--overwrite", action="store_true")
    return parser


def _custom_palette_command(args: argparse.Namespace) -> int:
    store = CustomPaletteStore(args.store)
    store.load_all()
    command = args.custom_command
    if command == "analyze":
        analysis = analyze_palette(store.get(args.id))
        _print_analysis(analysis, as_json=args.json)
        return 0
    if command == "plan":
        plan = plan_format_conversion(store.get(args.id), args.target_format)
        _print_plan(plan, as_json=args.json)
        return 1 if plan.blocked else 0
    if command == "validate":
        plan = plan_hardware_conversion(store.get(args.id), get_hardware_target(args.target))
        _print_plan(plan, as_json=args.json)
        return 1 if plan.blocked else 0
    if command == "convert":
        palette = store.get(args.id)
        plan = plan_format_conversion(palette, args.target_format)
        _print_plan(plan, as_json=False)
        result = convert_interchange_palette(
            palette,
            args.output,
            format_id=args.target_format,
            policy=ExecutionPolicy(allow_metadata_loss=args.allow_metadata_loss),
            overwrite=args.overwrite,
            plan=plan,
        )
        print(f"Wrote {args.output}")
        _print_interchange_report(result.report.messages)
        return 0
    if command == "transform":
        if args.output.exists() and not args.overwrite:
            raise PaletteValidationError(f"Output already exists: {args.output}")
        palette = store.get(args.id)
        plan = plan_hardware_conversion(palette, get_hardware_target(args.target))
        _print_plan(plan, as_json=False)
        result = execute_plan(
            palette,
            plan,
            ExecutionPolicy(
                allow_channel_quantization=args.allow_channel_quantization,
                allow_color_reduction=args.allow_color_reduction,
                allow_index_changes=args.allow_index_changes,
                allow_fixed_palette_remap=args.allow_fixed_palette_remap,
            ),
        )
        save_native_palette(result.palette, args.output)
        print(f"Wrote {args.output}")
        return 0
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
    if command == "import-ilbm":
        result = import_ilbm_palette(
            args.file,
            palette_id=args.palette_id,
            name=args.name,
        )
        palette = store.add(result.palette)
        path = store.save(palette.id)
        print(f"Imported {len(palette.colors)} ordered CMAP entries as {palette.id}")
        _print_ilbm_document(result.document)
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


def _analysis_payload(analysis: PaletteAnalysis) -> dict[str, object]:
    statistics = analysis.statistics
    return {
        "palette_id": analysis.palette_id,
        "statistics": {
            "entry_count": statistics.entry_count,
            "unique_color_count": statistics.unique_color_count,
            "duplicate_entry_count": statistics.duplicate_entry_count,
            "duplicate_groups": [
                {"color": list(group.color), "indexes": list(group.indexes)}
                for group in statistics.duplicate_groups
            ],
            "channel_minima": list(statistics.channel_minima),
            "channel_maxima": list(statistics.channel_maxima),
            "luminance_minimum": statistics.luminance_minimum,
            "luminance_maximum": statistics.luminance_maximum,
            "fits_4bit_channels": statistics.fits_4bit_channels,
            "metadata_fields": list(statistics.metadata_fields),
        },
        "issues": [_issue_payload(issue) for issue in analysis.issues],
    }


def _issue_payload(issue: ValidationIssue) -> dict[str, object]:
    return {
        "code": issue.code.value,
        "severity": issue.severity.value,
        "message": issue.message,
        "affected_indexes": list(issue.affected_indexes),
        "metadata_fields": list(issue.metadata_fields),
    }


def _plan_payload(plan: ConversionPlan) -> dict[str, object]:
    return {
        "source_id": plan.source_id,
        "source_fingerprint": plan.source_fingerprint,
        "target_kind": plan.target_kind,
        "target_id": plan.target_id,
        "exactness": plan.exactness.value,
        "export_supported": plan.export_supported,
        "blocked": plan.blocked,
        "issues": [_issue_payload(issue) for issue in plan.issues],
        "transformations": [
            {
                "kind": transformation.kind.value,
                "reason": transformation.reason,
                "lossy": transformation.lossy,
                "automatic": transformation.automatic,
                "metadata_fields": list(transformation.metadata_fields),
                "color_changes": [
                    {
                        "index": change.index,
                        "before": list(change.before),
                        "after": list(change.after),
                    }
                    for change in transformation.color_changes
                ],
            }
            for transformation in plan.transformations
        ],
    }


def _print_analysis(analysis: PaletteAnalysis, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(_analysis_payload(analysis), sort_keys=True))
        return
    statistics = analysis.statistics
    print(
        f"Palette {analysis.palette_id}: {statistics.entry_count} entries, "
        f"{statistics.unique_color_count} unique"
    )
    print(f"Duplicate entries: {statistics.duplicate_entry_count}")
    print(f"Fits 4-bit/channel: {'yes' if statistics.fits_4bit_channels else 'no'}")
    for issue in analysis.issues:
        print(f"{issue.severity.value.upper()} [{issue.code}] {issue.message}")


def _print_plan(plan: ConversionPlan, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(_plan_payload(plan), sort_keys=True))
        return
    print(f"Plan: {plan.source_id} -> {plan.target_kind}:{plan.target_id}")
    print(f"Exactness: {plan.exactness.value}")
    for issue in plan.issues:
        print(f"{issue.severity.value.upper()} [{issue.code}] {issue.message}")
    for transformation in plan.transformations:
        support = "automatic" if transformation.automatic else "analysis-only"
        print(f"Transform: {transformation.kind.value} ({support}) — {transformation.reason}")


def _print_ilbm_document(document: IlbmDocument) -> None:
    print(f"FORM ILBM: {len(document.chunks)} chunks")
    print(
        "Chunk order: " + " ".join(chunk.id.decode("ascii", "replace") for chunk in document.chunks)
    )
    print(f"CMAP entries: {len(document.palette.colors) if document.palette else 0}")
    print(f"CRNG ranges: {len(document.color_cycles)}")
    for index, cycle in enumerate(document.color_cycles):
        state = "enabled" if cycle.enabled else "disabled"
        direction = "reverse" if cycle.reversed else "forward"
        print(
            f"  {index}: indexes {cycle.low}..{cycle.high}, rate={cycle.rate}, "
            f"flags=0x{cycle.flags:04X}, {state}, {direction}"
        )


def _ilbm_command(args: argparse.Namespace) -> int:
    if args.ilbm_command == "inspect":
        _print_ilbm_document(inspect_ilbm(args.input))
        return 0
    if args.ilbm_command == "replace-palette":
        store = CustomPaletteStore(args.store)
        store.load_all()
        palette = store.get(args.palette)
        result = replace_ilbm_palette(args.input, args.output, palette, overwrite=args.overwrite)
        print(f"Wrote {args.output}")
        for message in result.messages:
            print(message)
        return 0
    if args.ilbm_command == "cycles":
        document = inspect_ilbm(args.input)
        _print_cycles(document, as_json=args.json)
        return 0
    if args.ilbm_command == "cycle-at":
        document = inspect_ilbm(args.input)
        if document.palette is None:
            raise IlbmPaletteError("ILBM contains no CMAP palette")
        colors = palette_at(document.palette.colors, document.color_cycles, args.time)
        if args.json:
            print(
                json.dumps(
                    {
                        "time_seconds": float(args.time),
                        "colors": [list(color) for color in colors],
                    },
                    sort_keys=True,
                )
            )
        else:
            for index, color in enumerate(colors):
                print(f"{index}: #{color[0]:02X}{color[1]:02X}{color[2]:02X}")
        return 0
    if args.ilbm_command == "cycle-preview":
        if args.output.exists() and not args.overwrite:
            raise IlbmPaletteError(f"Output already exists: {args.output}")
        document = inspect_ilbm(args.input)
        if document.palette is None:
            raise IlbmPaletteError("ILBM contains no CMAP palette")
        indexed = decode_indexed_ilbm(document)
        colors = palette_at(document.palette.colors, document.color_cycles, args.time)
        image = render_indexed_preview(indexed, colors)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.save(args.output)
        print(f"Wrote {args.output}; indexed pixels remained unchanged")
        return 0
    if args.ilbm_command == "cycle-add":
        cycle = ColorCycleRange.create(
            rate=args.rate,
            low=args.low,
            high=args.high,
            active=args.active,
            reverse=args.reverse,
        )
        result = add_ilbm_cycle(args.input, args.output, cycle, overwrite=args.overwrite)
        print(result.messages[0])
        return 0
    if args.ilbm_command == "cycle-set":
        document = inspect_ilbm(args.input)
        if not 0 <= args.index < len(document.color_cycles):
            raise IlbmPaletteError(f"CRNG index out of range: {args.index}")
        cycle = document.color_cycles[args.index].edited(
            rate=args.rate,
            low=args.low,
            high=args.high,
            active=args.active,
            reverse=args.reverse,
        )
        result = edit_ilbm_cycle(
            args.input, args.output, args.index, cycle, overwrite=args.overwrite
        )
        print(result.messages[0])
        return 0
    if args.ilbm_command == "cycle-remove":
        result = remove_ilbm_cycle(args.input, args.output, args.index, overwrite=args.overwrite)
        print(result.messages[0])
        return 0
    raise IlbmPaletteError(f"Unknown ILBM command: {args.ilbm_command}")


def _print_cycles(document: IlbmDocument, *, as_json: bool) -> None:
    palette_size = len(document.palette.colors) if document.palette is not None else 0
    issues = validate_cycles(document.color_cycles, palette_size)
    unsupported = [
        chunk.id.decode("ascii", "replace")
        for chunk in document.chunks
        if chunk.id in {b"DRNG", b"BRNG"}
    ]
    payload = {
        "cycles": [
            {
                "index": index,
                "active": cycle.enabled,
                "reverse": cycle.reversed,
                "rate": cycle.rate,
                "steps_per_second": cycle.steps_per_second,
                "seconds_per_step": cycle.seconds_per_step,
                "low": cycle.low,
                "high": cycle.high,
                "length": cycle.range_length,
                "reserved": cycle.reserved,
                "flags": cycle.flags,
            }
            for index, cycle in enumerate(document.color_cycles)
        ],
        "issues": [
            {
                "code": issue.code.value,
                "severity": issue.severity.value,
                "message": issue.message,
                "range_indexes": list(issue.range_indexes),
            }
            for issue in issues
        ],
        "unsupported_cycle_chunks": unsupported,
    }
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    for index, cycle in enumerate(document.color_cycles):
        print(
            f"{index}: indexes {cycle.low}..{cycle.high}, "
            f"rate={cycle.rate}, {cycle.steps_per_second:.6g} steps/s, "
            f"{'active' if cycle.enabled else 'inactive'}, "
            f"{'reverse' if cycle.reversed else 'forward'}"
        )
    for issue in issues:
        print(f"{issue.severity.value.upper()} [{issue.code.value}] {issue.message}")
    if unsupported:
        print("Warning: preserved but not simulated: " + ", ".join(unsupported))


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
        except (
            OSError,
            CustomPaletteError,
            NativePaletteError,
            PaletteCodecError,
            PaletteValidationError,
        ) as exc:
            parser.error(str(exc))
    if args.command == "ilbm":
        try:
            return _ilbm_command(args)
        except (OSError, CustomPaletteError, IlbmPaletteError) as exc:
            parser.error(str(exc))
    parser.error(f"Unknown command: {args.command}")
    return 2
