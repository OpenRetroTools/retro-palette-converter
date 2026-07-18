"""Batch image conversion services."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from retropal.core.converter import convert_file
from retropal.core.models import DitherMode

SUPPORTED_IMAGE_SUFFIXES = frozenset({".bmp", ".jpeg", ".jpg", ".png"})


@dataclass(frozen=True, slots=True)
class BatchFailure:
    """A source image that could not be converted."""

    source: Path
    message: str


@dataclass(frozen=True, slots=True)
class BatchResult:
    """Summary of a batch conversion operation."""

    converted: tuple[Path, ...]
    skipped: tuple[Path, ...]
    failures: tuple[BatchFailure, ...]
    cancelled: bool = False

    @property
    def success(self) -> bool:
        return not self.failures


def discover_images(input_dir: Path, *, recursive: bool = True) -> tuple[Path, ...]:
    """Return supported image files below *input_dir* in deterministic order."""

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input path is not a directory: {input_dir}")

    candidates: Iterable[Path]
    candidates = input_dir.rglob("*") if recursive else input_dir.iterdir()

    return tuple(
        sorted(
            (
                path
                for path in candidates
                if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
            ),
            key=lambda path: path.relative_to(input_dir).as_posix().lower(),
        )
    )


def output_path_for(source: Path, input_dir: Path, output_dir: Path) -> Path:
    """Map a source path to a PNG path while preserving relative directories."""

    return (output_dir / source.relative_to(input_dir)).with_suffix(".png")


def convert_batch(
    input_dir: Path,
    output_dir: Path,
    palette_id: str,
    dither: DitherMode = DitherMode.NONE,
    *,
    recursive: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
    progress: Callable[[int, Path], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> BatchResult:
    """Convert supported images below *input_dir* to PNG files in *output_dir*."""

    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    sources = discover_images(input_dir, recursive=recursive)

    converted: list[Path] = []
    skipped: list[Path] = []
    failures: list[BatchFailure] = []

    cancelled = False
    for index, source in enumerate(sources, start=1):
        if is_cancelled is not None and is_cancelled():
            cancelled = True
            break
        if progress is not None:
            progress(index, source)
        # Avoid treating an existing output tree as new input when it lives below input_dir.
        if source.is_relative_to(output_dir):
            continue

        target = output_path_for(source, input_dir, output_dir)
        if target.exists() and not overwrite:
            skipped.append(target)
            continue

        if dry_run:
            converted.append(target)
            continue

        try:
            convert_file(source, target, palette_id, dither)
        except (OSError, ValueError) as exc:
            failures.append(BatchFailure(source=source, message=str(exc)))
        else:
            converted.append(target)

    return BatchResult(
        converted=tuple(converted),
        skipped=tuple(skipped),
        failures=tuple(failures),
        cancelled=cancelled,
    )
