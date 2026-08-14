"""Deterministic Deluxe Paint CRNG validation and palette-state evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from retropal.palettes.amiga_iff.base import ColorCycleRange
from retropal.palettes.base import RGBColor


class CycleIssueSeverity(StrEnum):
    INFORMATIONAL = "informational"
    WARNING = "warning"
    BLOCKING = "blocking"


class CycleIssueCode(StrEnum):
    SINGLE_ENTRY = "crng-single-entry"
    INDEX_OUT_OF_BOUNDS = "crng-index-out-of-bounds"
    OVERLAPPING_ACTIVE_RANGES = "crng-overlapping-active-ranges"
    ZERO_RATE = "crng-zero-rate"
    DPAINT_NO_RATE = "crng-dpaint-no-rate"
    UNKNOWN_FLAGS = "crng-unknown-flags"


@dataclass(frozen=True, slots=True)
class CycleValidationIssue:
    code: CycleIssueCode
    severity: CycleIssueSeverity
    message: str
    range_indexes: tuple[int, ...]


def validate_cycles(
    ranges: tuple[ColorCycleRange, ...], palette_size: int
) -> tuple[CycleValidationIssue, ...]:
    issues: list[CycleValidationIssue] = []
    for index, cycle in enumerate(ranges):
        if cycle.high >= palette_size:
            issues.append(
                CycleValidationIssue(
                    CycleIssueCode.INDEX_OUT_OF_BOUNDS,
                    CycleIssueSeverity.BLOCKING,
                    f"CRNG {index} index {cycle.high} exceeds palette size {palette_size}.",
                    (index,),
                )
            )
        if cycle.range_length == 1:
            issues.append(
                CycleValidationIssue(
                    CycleIssueCode.SINGLE_ENTRY,
                    CycleIssueSeverity.INFORMATIONAL,
                    f"CRNG {index} contains one entry and cannot visibly cycle.",
                    (index,),
                )
            )
        if cycle.rate == 0:
            issues.append(
                CycleValidationIssue(
                    CycleIssueCode.ZERO_RATE,
                    CycleIssueSeverity.WARNING,
                    f"CRNG {index} has zero rate and is stationary.",
                    (index,),
                )
            )
        elif cycle.enabled and cycle.rate == 36:
            issues.append(
                CycleValidationIssue(
                    CycleIssueCode.DPAINT_NO_RATE,
                    CycleIssueSeverity.WARNING,
                    f"CRNG {index} uses the historical Deluxe Paint no-cycle rate convention.",
                    (index,),
                )
            )
        if cycle.flags & ~3:
            issues.append(
                CycleValidationIssue(
                    CycleIssueCode.UNKNOWN_FLAGS,
                    CycleIssueSeverity.WARNING,
                    f"CRNG {index} contains reserved flag bits 0x{cycle.flags & ~3:04X}.",
                    (index,),
                )
            )
    active = [
        (index, cycle)
        for index, cycle in enumerate(ranges)
        if cycle.enabled and cycle.rate not in {0, 36} and cycle.range_length > 1
    ]
    for position, (left_index, left) in enumerate(active):
        for right_index, right in active[position + 1 :]:
            if max(left.low, right.low) <= min(left.high, right.high):
                issues.append(
                    CycleValidationIssue(
                        CycleIssueCode.OVERLAPPING_ACTIVE_RANGES,
                        CycleIssueSeverity.WARNING,
                        f"Active CRNG ranges {left_index} and {right_index} overlap; "
                        "stored chunk order determines composition.",
                        (left_index, right_index),
                    )
                )
    return tuple(issues)


def cycle_step(cycle: ColorCycleRange, elapsed_seconds: Fraction | float | int) -> int:
    """Return absolute steps using CRNG's rate * 60 / 2^14 units."""
    elapsed = (
        elapsed_seconds if isinstance(elapsed_seconds, Fraction) else Fraction(str(elapsed_seconds))
    )
    if elapsed < 0:
        raise ValueError("Elapsed time must not be negative")
    if not cycle.enabled or cycle.rate in {0, 36} or cycle.range_length <= 1:
        return 0
    return (elapsed.numerator * cycle.rate * 60) // (elapsed.denominator * 16384)


def palette_at(
    colors: tuple[RGBColor, ...],
    ranges: tuple[ColorCycleRange, ...],
    elapsed_seconds: Fraction | float | int,
) -> tuple[RGBColor, ...]:
    """Apply ranges in stored order without changing the base palette."""
    result = list(colors)
    for cycle in ranges:
        if cycle.high >= len(result):
            continue
        steps = cycle_step(cycle, elapsed_seconds) % cycle.range_length
        if not steps:
            continue
        segment = result[cycle.low : cycle.high + 1]
        if cycle.reversed:
            rotated = segment[steps:] + segment[:steps]
        else:
            rotated = segment[-steps:] + segment[:-steps]
        result[cycle.low : cycle.high + 1] = rotated
    return tuple(result)
