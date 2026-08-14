from __future__ import annotations

import struct
from pathlib import Path

import pytest

from retropal.palettes.amiga_iff import (
    IffChunk,
    IlbmPaletteError,
    import_ilbm_palette,
    parse_ilbm,
    replace_ilbm_palette,
    serialize_ilbm,
)
from retropal.palettes.custom import CustomPalette
from retropal.palettes.native import load_native_palette
from retropal.palettes.store import CustomPaletteStore
from tests.ilbm_fixtures import crng, iff_chunk, ilbm_form, rich_ilbm

COLORS = ((1, 2, 3), (255, 0, 128), (1, 2, 3))


def test_parse_preserves_chunk_order_payloads_padding_and_duplicate_cmap() -> None:
    data = rich_ilbm()
    document = parse_ilbm(data, palette_id="fixture", palette_name="Fixture")

    assert document.form_type == b"ILBM"
    assert [chunk.id for chunk in document.chunks] == [
        b"ANNO",
        b"CRNG",
        b"BMHD",
        b"XXXX",
        b"CMAP",
        b"AUTH",
        b"CRNG",
        b"BODY",
    ]
    assert document.palette is not None
    assert document.palette.colors == COLORS
    assert document.chunks[0].pad_byte == b"\x7f"
    assert document.chunks[-1].payload == b"\xaa\xbb\xcc"
    assert serialize_ilbm(document) == data


def test_form_and_chunk_lengths_are_big_endian_and_exclude_padding() -> None:
    data = rich_ilbm()
    anno_offset = 12
    assert data[4:8] == struct.pack(">I", len(data) - 8)
    assert data[anno_offset : anno_offset + 4] == b"ANNO"
    assert data[anno_offset + 4 : anno_offset + 8] == b"\x00\x00\x00\x03"
    assert data[anno_offset + 8 : anno_offset + 12] == b"odd\x7f"


def test_crng_fields_multiple_order_and_raw_payload() -> None:
    document = parse_ilbm(rich_ilbm())
    first, second = document.color_cycles

    assert (first.rate, first.flags, first.low, first.high, first.reserved) == (273, 1, 1, 3, 0)
    assert first.enabled and not first.reversed
    assert (second.rate, second.flags, second.low, second.high, second.reserved) == (
        8192,
        3,
        4,
        7,
        0x1234,
    )
    assert second.enabled and second.reversed
    assert second.raw_payload == crng(8192, 3, 4, 7, reserved=0x1234)


def test_replacing_cmap_preserves_every_other_chunk_byte_for_byte(tmp_path: Path) -> None:
    source = tmp_path / "source.iff"
    output = tmp_path / "updated.iff"
    source.write_bytes(rich_ilbm())
    replacement = CustomPalette(
        "replacement", "Replacement", ((9, 8, 7), (9, 8, 7), (6, 5, 4), (3, 2, 1))
    )

    result = replace_ilbm_palette(source, output, replacement)
    before = parse_ilbm(source.read_bytes())
    after = parse_ilbm(output.read_bytes())

    assert after.palette is not None and after.palette.colors == replacement.colors
    assert [chunk.id for chunk in after.chunks] == [chunk.id for chunk in before.chunks]
    for old, new in zip(before.chunks, after.chunks, strict=True):
        if old.id != b"CMAP":
            assert new == old
    assert [cycle.raw_payload for cycle in after.color_cycles] == [
        cycle.raw_payload for cycle in before.color_cycles
    ]
    assert struct.unpack_from(">I", result.data, 4)[0] == len(result.data) - 8


def test_adding_missing_cmap_inserts_immediately_before_body(tmp_path: Path) -> None:
    source = tmp_path / "no-cmap.iff"
    output = tmp_path / "with-cmap.iff"
    source.write_bytes(ilbm_form(iff_chunk(b"BMHD", bytes(20)), iff_chunk(b"BODY", b"\x01\x02")))
    palette = CustomPalette("added", "Added", ((1, 2, 3),))

    replace_ilbm_palette(source, output, palette)
    updated = parse_ilbm(output.read_bytes())

    assert [chunk.id for chunk in updated.chunks] == [b"BMHD", b"CMAP", b"BODY"]
    assert updated.chunks[1].payload == b"\x01\x02\x03"
    assert updated.chunks[1].pad_byte == b"\0"


def test_multiple_cmap_uses_and_replaces_last_before_body(tmp_path: Path) -> None:
    data = ilbm_form(
        iff_chunk(b"CMAP", b"\0\0\0"),
        iff_chunk(b"ANNO", b"between"),
        iff_chunk(b"CMAP", b"\x01\x02\x03\x01\x02\x03"),
        iff_chunk(b"BODY", b"data"),
    )
    source = tmp_path / "multiple.iff"
    output = tmp_path / "multiple-out.iff"
    source.write_bytes(data)
    imported = import_ilbm_palette(source)
    assert imported.palette.colors == ((1, 2, 3), (1, 2, 3))
    assert any("last CMAP" in message for message in imported.messages)

    replace_ilbm_palette(source, output, CustomPalette("new", "New", ((4, 5, 6),)), overwrite=False)
    updated = parse_ilbm(output.read_bytes())
    assert updated.chunks[0].payload == b"\0\0\0"
    assert updated.chunks[2].payload == b"\x04\x05\x06"


def test_import_to_native_reports_ilbm_metadata_loss(tmp_path: Path) -> None:
    source = tmp_path / "My Picture.iff"
    source.write_bytes(rich_ilbm())
    result = import_ilbm_palette(source)
    store = CustomPaletteStore(tmp_path / "store")
    store.add(result.palette)
    saved = store.save(result.palette.id)

    assert result.palette.id == "my-picture"
    assert result.palette.source == "CMAP imported from ILBM My Picture.iff"
    assert load_native_palette(saved) == result.palette
    assert any("not stored" in message for message in result.messages)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"NOPE" + rich_ilbm()[4:], "signature"),
        (b"FORM\0\0", "Truncated"),
        (rich_ilbm()[:-1], "FORM size"),
        (ilbm_form(iff_chunk(b"CMAP", b"\0\0\0"), form_type=b"8SVX"), "FORM type"),
        (b"FORM\0\0\0\x07ILBMabc", "chunk header"),
        (
            ilbm_form(b"CMAP" + struct.pack(">I", 9)),
            "exceeds FORM bounds",
        ),
        (ilbm_form(iff_chunk(b"CMAP", b"\0\0")), "complete RGB triples"),
        (ilbm_form(iff_chunk(b"CRNG", b"\0" * 7)), "exactly 8"),
        (
            ilbm_form(iff_chunk(b"BODY", b"body"), iff_chunk(b"CMAP", b"\0\0\0")),
            "after BODY",
        ),
    ],
)
def test_malformed_or_unsupported_ilbm_is_controlled(data: bytes, message: str) -> None:
    with pytest.raises(IlbmPaletteError, match=message):
        parse_ilbm(data)


def test_missing_odd_pad_is_rejected() -> None:
    data = rich_ilbm()
    malformed = data[:-1]
    malformed = malformed[:4] + struct.pack(">I", len(malformed) - 8) + malformed[8:]
    with pytest.raises(IlbmPaletteError, match="pad byte"):
        parse_ilbm(malformed)


def test_import_requires_cmap(tmp_path: Path) -> None:
    path = tmp_path / "no-palette.iff"
    path.write_bytes(ilbm_form(iff_chunk(b"BODY", b"body")))
    with pytest.raises(IlbmPaletteError, match="no CMAP"):
        import_ilbm_palette(path)


def test_output_overwrite_is_explicit(tmp_path: Path) -> None:
    source = tmp_path / "source.iff"
    output = tmp_path / "output.iff"
    source.write_bytes(rich_ilbm())
    output.write_bytes(b"existing")
    with pytest.raises(IlbmPaletteError, match="already exists"):
        replace_ilbm_palette(source, output, CustomPalette("p", "P", ((0, 0, 0),)))


def test_iff_chunk_validates_alignment() -> None:
    with pytest.raises(IlbmPaletteError, match="alignment"):
        IffChunk(b"ODD!", b"x")
