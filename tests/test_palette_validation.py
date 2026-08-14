from __future__ import annotations

import json
from pathlib import Path

import pytest

from retropal.cli import main
from retropal.palettes.custom import CustomPalette
from retropal.palettes.interchange.service import convert_palette
from retropal.palettes.store import CustomPaletteStore
from retropal.palettes.validation import (
    Exactness,
    ExecutionPolicy,
    IssueCode,
    IssueSeverity,
    PaletteValidationError,
    TransformationKind,
    ValidationIssue,
    analyze_palette,
    fixed_palette_target,
    get_hardware_target,
    plan_format_conversion,
    plan_hardware_conversion,
)


def palette(
    colors: tuple[tuple[int, int, int], ...] = ((17, 34, 51), (255, 0, 170)),
    *,
    metadata: bool = True,
) -> CustomPalette:
    return CustomPalette(
        "test-palette",
        "Test Palette",
        colors,
        "Description" if metadata else "",
        "Provenance" if metadata else None,
    )


def test_analysis_statistics_duplicate_indexes_and_metadata() -> None:
    source = palette(((0, 0, 0), (255, 16, 8), (0, 0, 0)))
    result = analyze_palette(source)

    assert result.statistics.entry_count == 3
    assert result.statistics.unique_color_count == 2
    assert result.statistics.duplicate_entry_count == 1
    assert result.statistics.duplicate_groups[0].indexes == (0, 2)
    assert result.statistics.channel_minima == (0, 0, 0)
    assert result.statistics.channel_maxima == (255, 16, 8)
    assert result.statistics.metadata_fields == ("id", "name", "description", "source")
    assert result.issues[0].code == "duplicate-rgb-entries"


def test_json_is_exact_and_gpl_jasc_report_metadata_loss() -> None:
    source = palette()
    assert plan_format_conversion(source, "json").exactness is Exactness.EXACT
    gpl = plan_format_conversion(source, "gpl")
    jasc = plan_format_conversion(source, "jasc")

    assert gpl.exactness is Exactness.METADATA_LOSS
    assert gpl.issues[0].metadata_fields == ("id", "description", "source")
    assert jasc.issues[0].metadata_fields == ("id", "name", "description", "source")
    assert gpl.transformations[0].kind is TransformationKind.STRIP_METADATA


def test_act_padding_is_exact_for_rgb_but_overflow_is_analysis_only() -> None:
    exact = plan_format_conversion(palette(metadata=False), "act")
    assert exact.exactness is Exactness.METADATA_LOSS  # ACT cannot preserve ID/name.
    assert exact.issues[-1].code == "target-format-padding"
    assert exact.transformations[-1].kind is TransformationKind.FORMAT_ENCODING
    overflow = plan_format_conversion(
        palette(tuple((index % 256, 0, 0) for index in range(257)), metadata=False), "act"
    )
    assert overflow.blocked
    assert overflow.issues[-1].code == "target-color-count-exceeded"
    assert not overflow.transformations[-1].automatic


def test_brilliance_export_is_unsupported() -> None:
    plan = plan_format_conversion(palette(), "brilliance-plt")
    assert plan.exactness is Exactness.UNSUPPORTED
    assert plan.blocked
    assert plan.issues[0].code == "target-export-unsupported"


def test_ocs_exact_precision_mismatch_and_count_overflow() -> None:
    target = get_hardware_target("amiga-ocs-32")
    assert plan_hardware_conversion(palette(), target).exactness is Exactness.EXACT
    mismatch = plan_hardware_conversion(palette(((18, 52, 86),), metadata=False), target)
    change = mismatch.transformations[0].color_changes[0]
    assert mismatch.exactness is Exactness.RGB_LOSS
    assert change.before == (18, 52, 86)
    assert change.after == (17, 51, 85)
    overflow = plan_hardware_conversion(
        palette(tuple((index, index, index) for index in range(33)), metadata=False), target
    )
    assert overflow.blocked
    assert any(issue.code == "target-color-count-exceeded" for issue in overflow.issues)


def test_fixed_palette_exact_and_explicit_rgb_distance_remap() -> None:
    target = fixed_palette_target("gameboy-dmg")
    exact_color = (15, 56, 15)
    assert (
        plan_hardware_conversion(palette((exact_color,), metadata=False), target).exactness
        is Exactness.EXACT
    )
    plan = plan_hardware_conversion(palette(((1, 2, 3),), metadata=False), target)
    assert plan.issues[0].code == "fixed-palette-color-mismatch"
    assert plan.transformations[0].kind is TransformationKind.REMAP_FIXED_PALETTE
    assert "RGB distance" in plan.transformations[0].reason


def test_lossy_execution_is_blocked_then_explicit_and_source_is_immutable() -> None:
    source = palette(((18, 52, 86),), metadata=False)
    plan = plan_hardware_conversion(source, get_hardware_target("amiga-ocs-16"))
    with pytest.raises(PaletteValidationError, match="explicit permission"):
        from retropal.palettes.validation import execute_plan

        execute_plan(source, plan)
    from retropal.palettes.validation import execute_plan

    result = execute_plan(source, plan, ExecutionPolicy(allow_channel_quantization=True))
    assert source.colors == ((18, 52, 86),)
    assert result.palette.colors == ((17, 51, 85),)


def test_plan_cannot_execute_against_changed_palette_with_same_id() -> None:
    from retropal.palettes.validation import execute_plan

    source = palette(metadata=False)
    plan = plan_format_conversion(source, "json")
    changed = source.set_color(0, (0, 0, 0))

    with pytest.raises(PaletteValidationError, match="does not match source"):
        execute_plan(changed, plan)


def test_format_conversion_blocks_loss_before_writing_then_allows_it(tmp_path: Path) -> None:
    source = palette()
    output = tmp_path / "palette.gpl"
    plan = plan_format_conversion(source, "gpl")
    with pytest.raises(PaletteValidationError, match="Metadata loss"):
        convert_palette(source, output, format_id="gpl", plan=plan)
    assert not output.exists()

    convert_palette(
        source,
        output,
        format_id="gpl",
        plan=plan,
        policy=ExecutionPolicy(allow_metadata_loss=True),
    )
    assert output.read_bytes().startswith(b"GIMP Palette\n")
    assert source.description == "Description"


def test_duplicates_and_order_survive_exact_execution(tmp_path: Path) -> None:
    source = palette(((0, 0, 0), (255, 0, 0), (0, 0, 0)))
    output = tmp_path / "palette.json"
    convert_palette(source, output, format_id="json")
    payload = json.loads(output.read_text())
    assert payload["colors"] == [[0, 0, 0], [255, 0, 0], [0, 0, 0]]


def test_cli_json_analysis_plan_block_and_approval(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    store_path = tmp_path / "store"
    store = CustomPaletteStore(store_path)
    store.add(palette())
    store.save("test-palette")

    assert (
        main(["custom-palettes", "--store", str(store_path), "analyze", "test-palette", "--json"])
        == 0
    )
    analysis = json.loads(capsys.readouterr().out)
    assert analysis["statistics"]["entry_count"] == 2
    assert (
        main(
            [
                "custom-palettes",
                "--store",
                str(store_path),
                "plan",
                "test-palette",
                "--target-format",
                "gpl",
                "--json",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["exactness"] == "metadata-loss"

    blocked = tmp_path / "blocked.gpl"
    with pytest.raises(SystemExit):
        main(
            [
                "custom-palettes",
                "--store",
                str(store_path),
                "convert",
                "test-palette",
                "--target-format",
                "gpl",
                "--output",
                str(blocked),
            ]
        )
    assert not blocked.exists()
    output = tmp_path / "approved.gpl"
    assert (
        main(
            [
                "custom-palettes",
                "--store",
                str(store_path),
                "convert",
                "test-palette",
                "--target-format",
                "gpl",
                "--output",
                str(output),
                "--allow-metadata-loss",
            ]
        )
        == 0
    )
    assert output.exists()

    transformed = tmp_path / "ocs.retropal-palette.json"
    assert (
        main(
            [
                "custom-palettes",
                "--store",
                str(store_path),
                "transform",
                "test-palette",
                "--target",
                "amiga-ocs-16",
                "--output",
                str(transformed),
                "--allow-channel-quantization",
            ]
        )
        == 0
    )
    assert transformed.exists()


def test_external_metadata_boundaries_have_stable_issue_codes() -> None:
    indexed = ValidationIssue(
        IssueCode.INDEXED_TRANSPARENCY_NOT_PRESERVED,
        IssueSeverity.LOSSY,
        "Indexed alpha is external to CustomPalette.",
    )
    ilbm = ValidationIssue(
        IssueCode.ILBM_DOCUMENT_METADATA_NOT_PRESERVED,
        IssueSeverity.LOSSY,
        "CRNG and raw chunks are external to CustomPalette.",
    )
    indexed_plan = plan_format_conversion(palette(metadata=False), "json", source_issues=(indexed,))
    ilbm_plan = plan_format_conversion(palette(metadata=False), "json", source_issues=(ilbm,))
    assert indexed_plan.issues[0].code == "indexed-transparency-not-preserved"
    assert ilbm_plan.issues[0].code == "ilbm-document-metadata-not-preserved"
    assert indexed_plan.exactness is Exactness.METADATA_LOSS
