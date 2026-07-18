from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from retropal.core.batch import convert_batch, discover_images, output_path_for
from retropal.core.models import DitherMode


def make_image(path: Path, color: tuple[int, int, int, int] = (180, 90, 30, 255)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGBA", (3, 2), color)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        image = image.convert("RGB")
    image.save(path)


def test_discover_images_supports_common_formats_and_sorts_paths(tmp_path: Path) -> None:
    make_image(tmp_path / "z.png")
    make_image(tmp_path / "nested" / "a.bmp")
    make_image(tmp_path / "b.jpg")
    (tmp_path / "notes.txt").write_text("not an image")

    assert [path.relative_to(tmp_path).as_posix() for path in discover_images(tmp_path)] == [
        "b.jpg",
        "nested/a.bmp",
        "z.png",
    ]


def test_discover_images_can_be_non_recursive(tmp_path: Path) -> None:
    make_image(tmp_path / "top.png")
    make_image(tmp_path / "nested" / "child.png")

    assert discover_images(tmp_path, recursive=False) == (tmp_path / "top.png",)


def test_discover_images_validates_input_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        discover_images(tmp_path / "missing")

    source = tmp_path / "source.png"
    make_image(source)
    with pytest.raises(NotADirectoryError):
        discover_images(source)


def test_output_path_preserves_structure_and_uses_png(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    source = input_dir / "sprites" / "hero.jpg"
    assert output_path_for(source, input_dir, tmp_path / "output") == (
        tmp_path / "output" / "sprites" / "hero.png"
    )


def test_convert_batch_converts_images_and_preserves_directories(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    make_image(input_dir / "one.png")
    make_image(input_dir / "nested" / "two.jpg")

    result = convert_batch(input_dir, output_dir, "ega", DitherMode.NONE)

    assert result.success
    assert len(result.converted) == 2
    assert not result.skipped
    assert not result.failures
    assert (output_dir / "one.png").exists()
    assert (output_dir / "nested" / "two.png").exists()


def test_convert_batch_skips_existing_outputs_unless_overwrite_is_enabled(
    tmp_path: Path,
) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    make_image(input_dir / "one.png", (255, 0, 0, 255))
    make_image(output_dir / "one.png", (0, 0, 0, 255))

    skipped = convert_batch(input_dir, output_dir, "ega")
    assert skipped.converted == ()
    assert skipped.skipped == (output_dir.resolve() / "one.png",)

    overwritten = convert_batch(input_dir, output_dir, "ega", overwrite=True)
    assert overwritten.converted == (output_dir.resolve() / "one.png",)
    assert overwritten.skipped == ()


def test_convert_batch_dry_run_writes_nothing(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    make_image(input_dir / "one.png")

    result = convert_batch(input_dir, output_dir, "ega", dry_run=True)

    assert result.converted == (output_dir.resolve() / "one.png",)
    assert not output_dir.exists()


def test_convert_batch_records_invalid_images_and_continues(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    make_image(input_dir / "good.png")
    bad = input_dir / "bad.png"
    bad.write_text("not really a PNG")

    result = convert_batch(input_dir, output_dir, "ega")

    assert not result.success
    assert result.converted == (output_dir.resolve() / "good.png",)
    assert len(result.failures) == 1
    assert result.failures[0].source == bad.resolve()


def test_output_directory_inside_input_is_not_reprocessed(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = input_dir / "converted"
    make_image(input_dir / "source.png")
    make_image(output_dir / "old.png")

    result = convert_batch(input_dir, output_dir, "ega", overwrite=True)

    assert result.converted == (output_dir.resolve() / "source.png",)


def test_convert_batch_reports_progress(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    make_image(input_dir / "a.png")
    make_image(input_dir / "b.png")
    events: list[tuple[int, str]] = []

    result = convert_batch(
        input_dir,
        output_dir,
        "ega",
        progress=lambda index, source: events.append((index, source.name)),
    )

    assert result.success
    assert events == [(1, "a.png"), (2, "b.png")]


def test_convert_batch_can_be_cancelled_between_files(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    make_image(input_dir / "a.png")
    make_image(input_dir / "b.png")
    checks = 0

    def is_cancelled() -> bool:
        nonlocal checks
        checks += 1
        return checks > 1

    result = convert_batch(input_dir, output_dir, "ega", is_cancelled=is_cancelled)

    assert result.cancelled
    assert result.converted == (output_dir.resolve() / "a.png",)
    assert not (output_dir / "b.png").exists()
