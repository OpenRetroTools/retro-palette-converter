from __future__ import annotations

import json
import struct
from fractions import Fraction
from pathlib import Path

import pytest

from retropal.cli import main
from retropal.palettes.amiga_iff import (
    ColorCycleRange,
    IlbmPaletteError,
    cycle_step,
    decode_byterun1_rows,
    decode_indexed_ilbm,
    palette_at,
    parse_ilbm,
    render_indexed_preview,
    serialize_ilbm,
    validate_cycles,
)
from retropal.palettes.amiga_iff.service import write_cycle_document
from tests.ilbm_fixtures import bmhd, crng, iff_chunk, ilbm_form

A = (1, 0, 0)
B = (2, 0, 0)
C = (3, 0, 0)
D = (4, 0, 0)


def cycle(*, rate: int = 273, flags: int = 1, low: int = 0, high: int = 3) -> ColorCycleRange:
    payload = crng(rate, flags, low, high, reserved=0x1234)
    return ColorCycleRange(rate, flags, low, high, 0x1234, payload)


def indexed_fixture(
    *,
    width: int = 4,
    planes: int = 2,
    compression: int = 0,
    body: bytes | None = None,
    camg: int | None = None,
) -> bytes:
    # Indexes 0,1,2,3: plane 0 = 0101, plane 1 = 0011, word-padded.
    raw_body = body if body is not None else b"\x50\x00\x30\x00"
    chunks = [
        iff_chunk(b"BMHD", bmhd(width, 1, planes, compression=compression)),
        iff_chunk(b"CMAP", bytes(channel for color in (A, B, C, D) for channel in color)),
        iff_chunk(b"CRNG", crng(16384, 1, 0, 3)),
    ]
    if camg is not None:
        chunks.append(iff_chunk(b"CAMG", struct.pack(">I", camg)))
    chunks.append(iff_chunk(b"BODY", raw_body))
    return ilbm_form(*chunks)


def test_cycle_fields_edit_flags_reserved_and_raw_round_trip() -> None:
    original = cycle(flags=0x8001)
    changed = original.edited(active=False, reverse=True, rate=8192, low=1, high=2)

    assert not changed.enabled and changed.reversed
    assert changed.flags == 0x8002
    assert changed.reserved == 0x1234
    assert changed.raw_payload == crng(8192, 0x8002, 1, 2, reserved=0x1234)
    assert original.raw_payload == crng(273, 0x8001, 0, 3, reserved=0x1234)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"low": 4, "high": 3},
        {"low": -1, "high": 3},
        {"low": 0, "high": 256},
        {"low": 0, "high": 3, "rate": 65536},
    ],
)
def test_cycle_model_rejects_invalid_widths_and_ranges(kwargs: dict[str, int]) -> None:
    values = {"rate": 273, "low": 0, "high": 3, **kwargs}
    with pytest.raises(IlbmPaletteError):
        ColorCycleRange.create(active=True, reverse=False, **values)


def test_validation_inactive_single_overlap_bounds_and_unknown_flags() -> None:
    ranges = (
        cycle(rate=0, flags=0, low=0, high=0),
        cycle(rate=273, flags=0x8001, low=1, high=3),
        cycle(rate=273, flags=1, low=2, high=7),
    )
    codes = {issue.code.value for issue in validate_cycles(ranges, 4)}
    assert codes == {
        "crng-single-entry",
        "crng-zero-rate",
        "crng-unknown-flags",
        "crng-index-out-of-bounds",
        "crng-overlapping-active-ranges",
    }


def test_historical_timing_boundaries_and_large_time() -> None:
    one_hz = cycle(rate=273)
    sixty_hz = cycle(rate=16384)
    assert cycle_step(one_hz, Fraction(16384, 273 * 60) - Fraction(1, 1_000_000)) == 0
    assert cycle_step(one_hz, Fraction(16384, 273 * 60)) == 1
    assert cycle_step(sixty_hz, Fraction(1, 60)) == 1
    assert cycle_step(sixty_hz, 1000) == 60000
    assert cycle_step(cycle(rate=36), 1000) == 0
    assert cycle_step(cycle(rate=1), Fraction(16384, 60)) == 1
    with pytest.raises(ValueError, match="negative"):
        cycle_step(cycle(flags=0), -1)


def test_palette_at_forward_reverse_wrap_inactive_and_immutable() -> None:
    colors = (A, B, C, D)
    forward = cycle(rate=16384)
    reverse = cycle(rate=16384, flags=3)
    inactive = cycle(rate=16384, flags=0)
    assert palette_at(colors, (forward,), 0) == colors
    assert palette_at(colors, (forward,), Fraction(1, 60)) == (D, A, B, C)
    assert palette_at(colors, (reverse,), Fraction(1, 60)) == (B, C, D, A)
    assert palette_at(colors, (forward,), Fraction(4, 60)) == colors
    assert palette_at(colors, (inactive,), 10) == colors
    assert colors == (A, B, C, D)


def test_multiple_ranges_and_overlap_apply_in_stored_order() -> None:
    colors = (A, B, C, D, (5, 0, 0), (6, 0, 0))
    first = cycle(rate=16384, low=0, high=2)
    second = cycle(rate=16384, low=3, high=5)
    assert palette_at(colors, (first, second), Fraction(1, 60)) == (
        C,
        A,
        B,
        (6, 0, 0),
        D,
        (5, 0, 0),
    )
    overlap = cycle(rate=16384, low=1, high=3)
    assert palette_at(colors, (first, overlap), Fraction(1, 60)) == (
        C,
        D,
        A,
        B,
        (5, 0, 0),
        (6, 0, 0),
    )


def test_crng_edit_add_remove_preserves_all_unrelated_bytes(tmp_path: Path) -> None:
    data = ilbm_form(
        iff_chunk(b"ANNO", b"odd", pad=b"\x7f"),
        iff_chunk(b"CMAP", bytes(channel for color in (A, B, C, D) for channel in color)),
        iff_chunk(b"CRNG", crng(273, 1, 0, 3, reserved=9)),
        iff_chunk(b"CRNG", crng(8192, 0x4003, 1, 2, reserved=0xCAFE)),
        iff_chunk(b"DRNG", b"untouched"),
        iff_chunk(b"BRNG", b"also untouched"),
        iff_chunk(b"XXXX", b"unknown"),
        iff_chunk(b"BODY", b"body bytes"),
    )
    document = parse_ilbm(data)
    replacement = document.color_cycles[0].edited(rate=8192, reverse=True)
    edited = document.with_cycle_replaced(0, replacement)
    reparsed = parse_ilbm(serialize_ilbm(edited))

    for before, after in zip(document.chunks, reparsed.chunks, strict=True):
        if before.id != b"CRNG":
            assert after == before
    assert reparsed.color_cycles[1].raw_payload == document.color_cycles[1].raw_payload
    assert reparsed.color_cycles[0].reserved == 9
    assert reparsed.color_cycles[0].flags == 3
    added = edited.with_cycle_added(ColorCycleRange.create(rate=273, low=1, high=2))
    assert [chunk.id for chunk in added.chunks][-2:] == [b"XXXX", b"BODY"]
    assert added.with_cycle_removed(2).chunks == edited.chunks

    output = tmp_path / "edited.iff"
    write_cycle_document(edited, output)
    assert output.read_bytes() == serialize_ilbm(edited)


@pytest.mark.parametrize(
    ("compressed", "expected"),
    [
        (b"\x03abcd", b"abcd"),
        (b"\xfdx", b"xxxx"),
        (b"\x80\x03abcd", b"abcd"),
    ],
)
def test_byterun1_literal_repeat_and_noop(compressed: bytes, expected: bytes) -> None:
    assert decode_byterun1_rows(compressed, 4, 1) == expected


@pytest.mark.parametrize("data", [b"", b"\x03ab", b"\xfd", b"\x04abcde"])
def test_byterun1_rejects_underflow_truncation_and_overflow(data: bytes) -> None:
    with pytest.raises(IlbmPaletteError):
        decode_byterun1_rows(data, 4, 1)


def test_body_decoder_planes_padding_and_palette_only_rendering() -> None:
    document = parse_ilbm(indexed_fixture())
    indexed = decode_indexed_ilbm(document)
    assert indexed.pixel_indexes == (0, 1, 2, 3)
    before_indexes = indexed.pixel_indexes
    first = render_indexed_preview(indexed, (A, B, C, D))
    cycled = render_indexed_preview(indexed, (D, A, B, C))
    assert first.get_flattened_data() != cycled.get_flattened_data()
    assert indexed.pixel_indexes == before_indexes


@pytest.mark.parametrize("planes", [1, 2, 4, 5])
def test_body_decoder_supported_plane_counts(planes: int) -> None:
    row_bytes = 2
    document = parse_ilbm(indexed_fixture(width=1, planes=planes, body=bytes(row_bytes * planes)))
    assert decode_indexed_ilbm(document).pixel_indexes == (0,)


def test_body_decoder_byterun1_and_odd_width() -> None:
    raw = b"\x50\x00\x30\x00"
    compressed = b"\x01\x50\x00\x01\x30\x00"
    indexed = decode_indexed_ilbm(
        parse_ilbm(indexed_fixture(width=3, compression=1, body=compressed))
    )
    assert indexed.pixel_indexes == (0, 1, 2)
    assert decode_byterun1_rows(compressed, 2, 2) == raw


@pytest.mark.parametrize(
    ("masking", "body"),
    [
        (1, b"\x40\x00\x80\x00"),
        (2, b"\x40\x00"),
    ],
)
def test_body_decoder_mask_plane_and_transparent_index(masking: int, body: bytes) -> None:
    data = ilbm_form(
        iff_chunk(b"BMHD", bmhd(2, 1, 1, masking=masking, transparent=1)),
        iff_chunk(b"CMAP", bytes(channel for color in (A, B) for channel in color)),
        iff_chunk(b"BODY", body),
    )
    indexed = decode_indexed_ilbm(parse_ilbm(data))
    assert indexed.pixel_indexes == (0, 1)
    assert indexed.mask == (True, False)
    assert render_indexed_preview(indexed, (A, B)).getpixel((1, 0))[3] == 0


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (indexed_fixture(camg=0x0800), "HAM"),
        (indexed_fixture(camg=0x0080), "EHB"),
        (indexed_fixture(compression=2), "compression"),
        (indexed_fixture(planes=0, body=b""), "plane count"),
    ],
)
def test_unsupported_preview_does_not_prevent_crng_inspection(data: bytes, message: str) -> None:
    document = parse_ilbm(data)
    assert document.color_cycles
    with pytest.raises(IlbmPaletteError, match=message):
        decode_indexed_ilbm(document)


def test_cli_cycles_json_simulation_edit_and_preview(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "cycling.iff"
    source.write_bytes(indexed_fixture())
    assert main(["ilbm", "cycles", str(source), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["cycles"][0]["steps_per_second"] == 60
    assert main(["ilbm", "cycle-at", str(source), "--time", "1/60", "--json"]) == 0
    state = json.loads(capsys.readouterr().out)
    assert state["colors"][0] == list(D)

    edited = tmp_path / "edited.iff"
    assert (
        main(
            [
                "ilbm",
                "cycle-set",
                str(source),
                "0",
                "--output",
                str(edited),
                "--rate",
                "8192",
                "--reverse",
            ]
        )
        == 0
    )
    preview = tmp_path / "preview.png"
    assert (
        main(["ilbm", "cycle-preview", str(edited), "--time", "1", "--output", str(preview)]) == 0
    )
    assert preview.exists()
    before = parse_ilbm(source.read_bytes())
    after = parse_ilbm(edited.read_bytes())
    assert before.chunks[-1] == after.chunks[-1]
    with pytest.raises(SystemExit):
        main(["ilbm", "cycle-remove", str(source), "0", "--output", str(edited)])
    added = tmp_path / "added.iff"
    assert (
        main(
            [
                "ilbm",
                "cycle-add",
                str(source),
                "--output",
                str(added),
                "--rate",
                "273",
                "--low",
                "1",
                "--high",
                "2",
            ]
        )
        == 0
    )
    removed = tmp_path / "removed.iff"
    assert main(["ilbm", "cycle-remove", str(added), "1", "--output", str(removed)]) == 0
    assert len(parse_ilbm(removed.read_bytes()).color_cycles) == 1
