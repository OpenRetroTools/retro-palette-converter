"""Immutable palette analysis, conversion planning, and explicit execution."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from retropal.palettes import get_palette_info
from retropal.palettes.base import RGBColor
from retropal.palettes.custom import CustomPalette, CustomPaletteError
from retropal.palettes.fixed import load_fixed_palette
from retropal.palettes.interchange.base import metadata_loss
from retropal.palettes.interchange.registry import get_codec


class IssueSeverity(StrEnum):
    INFO = "informational"
    WARNING = "warning"
    LOSSY = "lossy"
    BLOCKING = "blocking"


class IssueCode(StrEnum):
    DUPLICATE_RGB_ENTRIES = "duplicate-rgb-entries"
    METADATA_NOT_PRESERVED = "metadata-not-preserved"
    TARGET_EXPORT_UNSUPPORTED = "target-export-unsupported"
    TARGET_COLOR_COUNT_EXCEEDED = "target-color-count-exceeded"
    CHANNEL_PRECISION_LOSS = "channel-precision-loss"
    FIXED_PALETTE_COLOR_MISMATCH = "fixed-palette-color-mismatch"
    INDEXED_TRANSPARENCY_NOT_PRESERVED = "indexed-transparency-not-preserved"
    ILBM_DOCUMENT_METADATA_NOT_PRESERVED = "ilbm-document-metadata-not-preserved"
    TARGET_FORMAT_PADDING = "target-format-padding"


class Exactness(StrEnum):
    EXACT = "exact"
    METADATA_LOSS = "metadata-loss"
    RGB_LOSS = "rgb-loss"
    INDEX_LOSS = "index-loss"
    MULTIPLE_LOSSES = "multiple-losses"
    UNSUPPORTED = "unsupported"
    IMPOSSIBLE = "impossible"


class TransformationKind(StrEnum):
    STRIP_METADATA = "strip-metadata"
    QUANTIZE_CHANNELS = "quantize-channels"
    REDUCE_COLORS = "reduce-colors"
    REMAP_FIXED_PALETTE = "remap-fixed-palette"
    FORMAT_ENCODING = "format-encoding"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: IssueCode
    severity: IssueSeverity
    message: str
    affected_indexes: tuple[int, ...] = ()
    metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DuplicateGroup:
    color: RGBColor
    indexes: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class PaletteStatistics:
    entry_count: int
    unique_color_count: int
    duplicate_entry_count: int
    duplicate_groups: tuple[DuplicateGroup, ...]
    channel_minima: RGBColor
    channel_maxima: RGBColor
    luminance_minimum: float
    luminance_maximum: float
    fits_4bit_channels: bool
    metadata_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PaletteAnalysis:
    palette_id: str
    statistics: PaletteStatistics
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True, slots=True)
class FormatTarget:
    format_id: str


@dataclass(frozen=True, slots=True)
class HardwareTarget:
    id: str
    name: str
    kind: Literal["programmable", "fixed"]
    maximum_colors: int
    channel_bits: int | None = None
    fixed_palette_id: str | None = None
    limitations: str = "Palette-only validation; rendering restrictions are not modeled."


PaletteTarget = FormatTarget | HardwareTarget


@dataclass(frozen=True, slots=True)
class ColorChange:
    index: int
    before: RGBColor
    after: RGBColor


@dataclass(frozen=True, slots=True)
class Transformation:
    kind: TransformationKind
    reason: str
    lossy: bool
    automatic: bool
    color_changes: tuple[ColorChange, ...] = ()
    metadata_fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ConversionPlan:
    source_id: str
    source_fingerprint: str
    target_kind: Literal["format", "hardware"]
    target_id: str
    exactness: Exactness
    issues: tuple[ValidationIssue, ...]
    transformations: tuple[Transformation, ...]
    export_supported: bool

    @property
    def blocked(self) -> bool:
        return any(issue.severity is IssueSeverity.BLOCKING for issue in self.issues)


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    allow_metadata_loss: bool = False
    allow_channel_quantization: bool = False
    allow_color_reduction: bool = False
    allow_index_changes: bool = False
    allow_fixed_palette_remap: bool = False


@dataclass(frozen=True, slots=True)
class ConversionResult:
    palette: CustomPalette
    plan: ConversionPlan


class PaletteValidationError(CustomPaletteError):
    """A controlled blocked or unsupported palette conversion."""


_HARDWARE_TARGETS = (
    HardwareTarget("amiga-ocs-16", "Amiga OCS 16", "programmable", 16, 4),
    HardwareTarget("amiga-ocs-32", "Amiga OCS 32", "programmable", 32, 4),
    HardwareTarget("amiga-ecs-64", "Amiga ECS 64", "programmable", 64, 4),
    HardwareTarget("amiga-aga-256", "Amiga AGA 256", "programmable", 256, 8),
)
_HARDWARE_BY_ID = {target.id: target for target in _HARDWARE_TARGETS}


def iter_hardware_targets() -> tuple[HardwareTarget, ...]:
    return _HARDWARE_TARGETS


def fixed_palette_target(palette_id: str) -> HardwareTarget:
    info = get_palette_info(palette_id)
    if info.adaptive:
        raise PaletteValidationError(f"Adaptive palette is not a fixed target: {palette_id}")
    return HardwareTarget(
        palette_id,
        info.name,
        "fixed",
        info.color_count,
        fixed_palette_id=palette_id,
    )


def get_hardware_target(target_id: str) -> HardwareTarget:
    if target_id in _HARDWARE_BY_ID:
        return _HARDWARE_BY_ID[target_id]
    try:
        return fixed_palette_target(target_id)
    except (KeyError, ValueError) as exc:
        raise PaletteValidationError(
            f"Unknown hardware or fixed-palette target: {target_id}"
        ) from exc


def _luminance(color: RGBColor) -> float:
    return (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000


def _palette_fingerprint(palette: CustomPalette) -> str:
    payload = {
        "id": palette.id,
        "name": palette.name,
        "colors": palette.colors,
        "description": palette.description,
        "source": palette.source,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def analyze_palette(palette: CustomPalette) -> PaletteAnalysis:
    indexes: dict[RGBColor, list[int]] = {}
    for index, color in enumerate(palette.colors):
        indexes.setdefault(color, []).append(index)
    duplicates = tuple(
        DuplicateGroup(color, tuple(color_indexes))
        for color, color_indexes in indexes.items()
        if len(color_indexes) > 1
    )
    metadata = (
        ("id", "name")
        + (("description",) if palette.description else ())
        + (("source",) if palette.source else ())
    )
    statistics = PaletteStatistics(
        len(palette.colors),
        len(indexes),
        len(palette.colors) - len(indexes),
        duplicates,
        (
            min(color[0] for color in palette.colors),
            min(color[1] for color in palette.colors),
            min(color[2] for color in palette.colors),
        ),
        (
            max(color[0] for color in palette.colors),
            max(color[1] for color in palette.colors),
            max(color[2] for color in palette.colors),
        ),
        min(map(_luminance, palette.colors)),
        max(map(_luminance, palette.colors)),
        all(channel % 17 == 0 for color in palette.colors for channel in color),
        metadata,
    )
    issues = tuple(
        ValidationIssue(
            IssueCode.DUPLICATE_RGB_ENTRIES,
            IssueSeverity.INFO,
            f"RGB {group.color} occurs at indexes {', '.join(map(str, group.indexes))}.",
            group.indexes,
        )
        for group in duplicates
    )
    return PaletteAnalysis(palette.id, statistics, issues)


def _quantize_channel(value: int, bits: int) -> int:
    levels = (1 << bits) - 1
    level = (value * levels + 127) // 255
    return (level * 255 + levels // 2) // levels


def _quantize_color(color: RGBColor, bits: int) -> RGBColor:
    return (
        _quantize_channel(color[0], bits),
        _quantize_channel(color[1], bits),
        _quantize_channel(color[2], bits),
    )


def _nearest_color(color: RGBColor, target_colors: tuple[RGBColor, ...]) -> RGBColor:
    return min(
        target_colors,
        key=lambda candidate: sum(
            (left - right) ** 2 for left, right in zip(color, candidate, strict=True)
        ),
    )


def plan_format_conversion(
    palette: CustomPalette,
    format_id: str,
    *,
    source_issues: tuple[ValidationIssue, ...] = (),
) -> ConversionPlan:
    codec = get_codec(format_id)
    if not codec.info.can_export:
        issue = ValidationIssue(
            IssueCode.TARGET_EXPORT_UNSUPPORTED,
            IssueSeverity.BLOCKING,
            f"{codec.info.name} export is unsupported.",
        )
        return ConversionPlan(
            palette.id,
            _palette_fingerprint(palette),
            "format",
            format_id,
            Exactness.UNSUPPORTED,
            (*source_issues, issue),
            (),
            False,
        )
    losses = metadata_loss(palette, codec.info.preserves)
    fields = tuple(
        field
        for field in ("id", "name", "description", "source")
        if field not in codec.info.preserves
        and (field in {"id", "name"} or bool(getattr(palette, field)))
    )
    issues = list(source_issues)
    transformations: list[Transformation] = []
    if losses:
        issues.append(
            ValidationIssue(
                IssueCode.METADATA_NOT_PRESERVED,
                IssueSeverity.LOSSY,
                "; ".join(losses),
                metadata_fields=fields,
            )
        )
        transformations.append(
            Transformation(
                TransformationKind.STRIP_METADATA,
                "The target codec cannot encode all populated palette metadata.",
                True,
                True,
                metadata_fields=fields,
            )
        )
    if (
        codec.info.padded_color_count is not None
        and len(palette.colors) < codec.info.padded_color_count
    ):
        issues.append(
            ValidationIssue(
                IssueCode.TARGET_FORMAT_PADDING,
                IssueSeverity.INFO,
                f"{codec.info.name} stores a {codec.info.padded_color_count}-entry table "
                "with an exact used-entry count.",
            )
        )
        transformations.append(
            Transformation(
                TransformationKind.FORMAT_ENCODING,
                "Codec padding preserves the declared palette entry count.",
                False,
                True,
            )
        )
    if codec.info.maximum_colors is not None and len(palette.colors) > codec.info.maximum_colors:
        issues.append(
            ValidationIssue(
                IssueCode.TARGET_COLOR_COUNT_EXCEEDED,
                IssueSeverity.BLOCKING,
                f"{codec.info.name} supports {codec.info.maximum_colors} entries; "
                f"source has {len(palette.colors)}.",
            )
        )
        transformations.append(
            Transformation(
                TransformationKind.REDUCE_COLORS,
                f"Colour reduction to at most {codec.info.maximum_colors} entries is required.",
                True,
                False,
            )
        )
    exactness = (
        Exactness.METADATA_LOSS
        if losses or any(issue.severity is IssueSeverity.LOSSY for issue in source_issues)
        else Exactness.EXACT
    )
    if any(issue.severity is IssueSeverity.BLOCKING for issue in issues):
        exactness = Exactness.IMPOSSIBLE
    return ConversionPlan(
        palette.id,
        _palette_fingerprint(palette),
        "format",
        format_id,
        exactness,
        tuple(issues),
        tuple(transformations),
        True,
    )


def plan_hardware_conversion(
    palette: CustomPalette,
    target: HardwareTarget,
    *,
    source_issues: tuple[ValidationIssue, ...] = (),
) -> ConversionPlan:
    issues = list(source_issues)
    transformations: list[Transformation] = []
    if len(palette.colors) > target.maximum_colors:
        issues.append(
            ValidationIssue(
                IssueCode.TARGET_COLOR_COUNT_EXCEEDED,
                IssueSeverity.BLOCKING,
                f"Target supports {target.maximum_colors} entries; "
                f"source has {len(palette.colors)}.",
            )
        )
        transformations.append(
            Transformation(
                TransformationKind.REDUCE_COLORS,
                "Colour reduction would change palette indexes.",
                True,
                False,
            )
        )
    if target.kind == "programmable" and target.channel_bits is not None:
        changes = tuple(
            ColorChange(index, color, quantized)
            for index, color in enumerate(palette.colors)
            if (quantized := _quantize_color(color, target.channel_bits)) != color
        )
        if changes:
            issues.append(
                ValidationIssue(
                    IssueCode.CHANNEL_PRECISION_LOSS,
                    IssueSeverity.LOSSY,
                    f"{len(changes)} entries require "
                    f"{target.channel_bits}-bit channel quantization.",
                    tuple(change.index for change in changes),
                )
            )
            transformations.append(
                Transformation(
                    TransformationKind.QUANTIZE_CHANNELS,
                    f"Quantize channels to {target.channel_bits} bits.",
                    True,
                    True,
                    changes,
                )
            )
    elif target.fixed_palette_id is not None:
        target_colors = load_fixed_palette(target.fixed_palette_id).colors
        changes = tuple(
            ColorChange(index, color, _nearest_color(color, target_colors))
            for index, color in enumerate(palette.colors)
            if color not in target_colors
        )
        if changes:
            issues.append(
                ValidationIssue(
                    IssueCode.FIXED_PALETTE_COLOR_MISMATCH,
                    IssueSeverity.LOSSY,
                    f"{len(changes)} entries are not present in the fixed target palette.",
                    tuple(change.index for change in changes),
                )
            )
            transformations.append(
                Transformation(
                    TransformationKind.REMAP_FIXED_PALETTE,
                    "Remap by squared Euclidean RGB distance.",
                    True,
                    True,
                    changes,
                )
            )
    lossy_kinds = {
        transformation.kind for transformation in transformations if transformation.lossy
    }
    if any(issue.severity is IssueSeverity.BLOCKING for issue in issues):
        exactness = Exactness.IMPOSSIBLE
    elif not lossy_kinds and not any(
        issue.severity is IssueSeverity.LOSSY for issue in source_issues
    ):
        exactness = Exactness.EXACT
    elif lossy_kinds == {TransformationKind.QUANTIZE_CHANNELS} or lossy_kinds == {
        TransformationKind.REMAP_FIXED_PALETTE
    }:
        exactness = Exactness.RGB_LOSS
    elif lossy_kinds == {TransformationKind.REDUCE_COLORS}:
        exactness = Exactness.INDEX_LOSS
    else:
        exactness = Exactness.MULTIPLE_LOSSES
    return ConversionPlan(
        palette.id,
        _palette_fingerprint(palette),
        "hardware",
        target.id,
        exactness,
        tuple(issues),
        tuple(transformations),
        True,
    )


def execute_plan(
    palette: CustomPalette, plan: ConversionPlan, policy: ExecutionPolicy | None = None
) -> ConversionResult:
    policy = policy or ExecutionPolicy()
    if palette.id != plan.source_id or _palette_fingerprint(palette) != plan.source_fingerprint:
        raise PaletteValidationError("Conversion plan does not match source palette")
    if not plan.export_supported:
        raise PaletteValidationError("Target export is unsupported")
    if plan.blocked:
        raise PaletteValidationError("Conversion plan is blocked")
    result = palette
    for transformation in plan.transformations:
        if not transformation.automatic:
            raise PaletteValidationError(f"Automatic {transformation.kind.value} is unsupported")
        if transformation.kind is TransformationKind.STRIP_METADATA:
            if not policy.allow_metadata_loss:
                raise PaletteValidationError("Metadata loss requires explicit permission")
        elif transformation.kind is TransformationKind.QUANTIZE_CHANNELS:
            if not policy.allow_channel_quantization:
                raise PaletteValidationError("Channel quantization requires explicit permission")
            colors = list(result.colors)
            for change in transformation.color_changes:
                colors[change.index] = change.after
            result = result.replace_colors(tuple(colors))
        elif transformation.kind is TransformationKind.REMAP_FIXED_PALETTE:
            if not policy.allow_fixed_palette_remap:
                raise PaletteValidationError("Fixed-palette remapping requires explicit permission")
            colors = list(result.colors)
            for change in transformation.color_changes:
                colors[change.index] = change.after
            result = result.replace_colors(tuple(colors))
        elif transformation.kind is TransformationKind.FORMAT_ENCODING:
            continue
        else:
            raise PaletteValidationError(f"Automatic {transformation.kind.value} is unsupported")
    return ConversionResult(result, plan)
