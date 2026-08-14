from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

from retropal.palettes.custom import CustomPalette
from retropal.palettes.interchange import PaletteCodecError, get_codec, iter_codecs
from retropal.palettes.interchange.json_codec import SCHEMA as JSON_SCHEMA
from retropal.palettes.interchange.registry import codec_for_export, identify_codec
from retropal.palettes.interchange.service import export_palette, import_palette


@pytest.fixture
def palette() -> CustomPalette:
    return CustomPalette(
        "ordered-duplicates",
        "Ordered, Duplicate Palette",
        ((1, 2, 3), (255, 0, 128), (1, 2, 3)),
        "Description that some formats cannot retain",
        "hand-authored fixture",
    )


@pytest.mark.parametrize("codec_id", ["gpl", "jasc", "riff-pal", "act", "json", "csv"])
def test_codecs_export_deterministically_and_preserve_ordered_duplicate_colors(
    codec_id: str,
    palette: CustomPalette,
) -> None:
    codec = get_codec(codec_id)

    first = codec.encode(palette)
    second = codec.encode(palette)
    imported = codec.decode(first.data, palette_id="imported", fallback_name="Imported")

    assert first.data == second.data
    assert imported.palette.colors == palette.colors
    assert imported.palette.colors[0] == imported.palette.colors[2]
    if codec_id == "json":
        assert imported.palette == palette
        assert first.report.lossless
    else:
        assert first.report.messages


def test_gpl_known_fixture_comments_whitespace_names_and_duplicates() -> None:
    fixture = b"""GIMP Palette
Name: Fixture Palette
Columns: 4
# normal comment
  1   2  3 First colour
255 0 128 Pink
1 2 3 Duplicate
"""

    result = get_codec("gpl").decode(fixture, palette_id="fixture", fallback_name="Fallback")

    assert result.palette.name == "Fixture Palette"
    assert result.palette.colors == ((1, 2, 3), (255, 0, 128), (1, 2, 3))
    assert result.report.messages == ("per-colour names are not represented by CustomPalette",)


@pytest.mark.parametrize(
    "fixture",
    [
        b"Not a palette\n1 2 3\n",
        b"GIMP Palette\nName: Test\n999 0 0 Bad\n",
        b"GIMP Palette\nName: Test\n1 2\n",
    ],
)
def test_gpl_rejects_malformed_input(fixture: bytes) -> None:
    with pytest.raises(PaletteCodecError):
        get_codec("gpl").decode(fixture, palette_id="fixture", fallback_name="Fixture")


def test_jasc_exact_fixture_and_crlf_export(palette: CustomPalette) -> None:
    fixture = b"JASC-PAL\r\n0100\r\n3\r\n1 2 3\r\n255 0 128\r\n1 2 3\r\n"
    codec = get_codec("jasc")

    imported = codec.decode(fixture, palette_id="jasc-fixture", fallback_name="JASC Fixture")
    exported = codec.encode(imported.palette)

    assert imported.palette.colors == palette.colors
    assert exported.data == fixture


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        (b"BAD\n0100\n1\n0 0 0\n", "signature"),
        (b"JASC-PAL\n0200\n1\n0 0 0\n", "version"),
        (b"JASC-PAL\n0100\n2\n0 0 0\n", "declares 2"),
        (b"JASC-PAL\n0100\n1\n0 0\n", "Malformed"),
        (b"JASC-PAL\n0100\n1\n0 0 999\n", "Invalid"),
    ],
)
def test_jasc_rejects_malformed_input(fixture: bytes, message: str) -> None:
    with pytest.raises(PaletteCodecError, match=message):
        get_codec("jasc").decode(fixture, palette_id="bad", fallback_name="Bad")


def riff_fixture(colors: tuple[tuple[int, int, int], ...]) -> bytes:
    logpalette = struct.pack("<HH", 0x0300, len(colors)) + b"".join(
        bytes((*color, 0)) for color in colors
    )
    chunk = b"data" + struct.pack("<I", len(logpalette)) + logpalette
    body = b"PAL " + chunk
    return b"RIFF" + struct.pack("<I", len(body)) + body


def test_riff_pal_exact_binary_fixture_and_byte_order(palette: CustomPalette) -> None:
    expected = riff_fixture(palette.colors)
    result = get_codec("riff-pal").encode(palette)

    assert result.data == expected
    assert result.data[4:8] == struct.pack("<I", len(expected) - 8)
    assert result.data[20:24] == b"\x00\x03\x03\x00"
    assert (
        get_codec("riff-pal")
        .decode(expected, palette_id="riff", fallback_name="RIFF")
        .palette.colors
        == palette.colors
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: b"NOPE" + data[4:], "signature"),
        (lambda data: data[:8] + b"WAVE" + data[12:], "form type"),
        (lambda data: data[:12] + b"JUNK" + data[16:], "Unsupported"),
        (lambda data: data[:-1], "size mismatch"),
        (lambda data: data[:16] + struct.pack("<I", 999) + data[20:], "Truncated"),
        (lambda data: data[:22] + struct.pack("<H", 4) + data[24:], "entry count"),
        (lambda data: data[:20] + b"\x01\x00" + data[22:], "version"),
    ],
)
def test_riff_pal_rejects_malformed_binary(mutate, message: str) -> None:
    fixture = riff_fixture(((1, 2, 3), (4, 5, 6), (1, 2, 3)))
    with pytest.raises(PaletteCodecError, match=message):
        get_codec("riff-pal").decode(
            mutate(fixture), palette_id="bad-riff", fallback_name="Bad RIFF"
        )


def test_riff_pal_reports_nonzero_entry_flags() -> None:
    fixture = bytearray(riff_fixture(((1, 2, 3),)))
    fixture[27] = 1
    result = get_codec("riff-pal").decode(bytes(fixture), palette_id="flags", fallback_name="Flags")
    assert result.report.messages == (
        "PALETTEENTRY usage flags are not represented by CustomPalette",
    )


def test_act_exact_772_byte_fixture_count_and_padding(palette: CustomPalette) -> None:
    result = get_codec("act").encode(palette)

    assert len(result.data) == 772
    assert result.data[:9] == bytes((1, 2, 3, 255, 0, 128, 1, 2, 3))
    assert result.data[9:768] == bytes(759)
    assert result.data[768:] == b"\x00\x03\xff\xff"
    assert (
        get_codec("act").decode(result.data, palette_id="act", fallback_name="ACT").palette.colors
        == palette.colors
    )


def test_act_768_byte_form_contains_256_colors() -> None:
    colors = tuple((index, index, index) for index in range(256))
    palette = CustomPalette("full-act", "Full ACT", colors)
    encoded = get_codec("act").encode(palette)

    assert len(encoded.data) == 768
    assert (
        get_codec("act")
        .decode(encoded.data, palette_id="full-act-import", fallback_name="ACT")
        .palette.colors
        == colors
    )


@pytest.mark.parametrize("size", [0, 767, 769, 771, 773])
def test_act_rejects_unsupported_sizes(size: int) -> None:
    with pytest.raises(PaletteCodecError, match="768 or 772"):
        get_codec("act").decode(bytes(size), palette_id="act", fallback_name="ACT")


def test_act_rejects_invalid_count_and_transparency() -> None:
    with pytest.raises(PaletteCodecError, match="colour count"):
        get_codec("act").decode(
            bytes(768) + b"\x00\x00\xff\xff", palette_id="act", fallback_name="ACT"
        )
    with pytest.raises(PaletteCodecError, match="transparency index"):
        get_codec("act").decode(
            bytes(768) + b"\x00\x02\x00\x02", palette_id="act", fallback_name="ACT"
        )


def test_act_rejects_more_than_256_colors() -> None:
    palette = CustomPalette("too-many", "Too Many", tuple((0, 0, 0) for _ in range(257)))
    with pytest.raises(PaletteCodecError, match="at most 256"):
        get_codec("act").encode(palette)


def test_json_interchange_schema_and_native_separation(palette: CustomPalette) -> None:
    codec = get_codec("json")
    exported = codec.encode(palette)
    payload = json.loads(exported.data)

    assert payload["schema"] == JSON_SCHEMA
    assert payload["schema"] != "org.openretrotools.retropal.custom-palette"
    assert (
        codec.decode(exported.data, palette_id="ignored", fallback_name="Ignored").palette
        == palette
    )


@pytest.mark.parametrize(
    "fixture",
    [
        b"not-json",
        b"{}",
        json.dumps({"schema": JSON_SCHEMA, "version": 99}).encode(),
    ],
)
def test_json_interchange_rejects_malformed_or_unsupported_data(fixture: bytes) -> None:
    with pytest.raises(PaletteCodecError):
        get_codec("json").decode(fixture, palette_id="json", fallback_name="JSON")


def test_csv_exact_fixture_quoting_and_duplicate_order() -> None:
    fixture = b'index,r,g,b\n"0","1","2","3"\n1,255,0,128\n2,1,2,3\n'
    result = get_codec("csv").decode(fixture, palette_id="csv", fallback_name="CSV Fixture")

    assert result.palette.colors == ((1, 2, 3), (255, 0, 128), (1, 2, 3))
    assert get_codec("csv").encode(result.palette).data == (
        b"index,r,g,b\n0,1,2,3\n1,255,0,128\n2,1,2,3\n"
    )


@pytest.mark.parametrize(
    ("fixture", "message"),
    [
        (b"r,g,b\n1,2,3\n", "header"),
        (b"index,r,g,b\n1,1,2,3\n", "index mismatch"),
        (b"index,r,g,b\n0,1,2\n", "4 columns"),
        (b"index,r,g,b\n0,1,2,999\n", "Invalid"),
        (b'index,r,g,b\n0,"1,2,3\n', "Malformed"),
    ],
)
def test_csv_rejects_malformed_rows(fixture: bytes, message: str) -> None:
    with pytest.raises(PaletteCodecError, match=message):
        get_codec("csv").decode(fixture, palette_id="csv", fallback_name="CSV")


def test_registry_has_unique_ids_and_only_intentional_pal_extension_ambiguity() -> None:
    codecs = iter_codecs()
    assert len({codec.info.id for codec in codecs}) == len(codecs)
    pal_codecs = {codec.info.id for codec in codecs if ".pal" in codec.info.extensions}
    assert pal_codecs == {"jasc", "riff-pal"}
    assert identify_codec(Path("palette.pal"), b"JASC-PAL\n0100\n1\n0 0 0\n").info.id == "jasc"
    assert identify_codec(Path("palette.pal"), riff_fixture(((0, 0, 0),))).info.id == "riff-pal"
    with pytest.raises(PaletteCodecError, match="Unsupported palette extension"):
        identify_codec(Path("palette.bin"), bytes(768))
    with pytest.raises(PaletteCodecError, match="ambiguous"):
        codec_for_export(Path("palette.pal"))


def test_registry_declares_format_capabilities() -> None:
    capabilities = {codec.info.id: set(codec.info.preserves) for codec in iter_codecs()}
    assert capabilities == {
        "gpl": {"name", "colors"},
        "jasc": {"colors"},
        "riff-pal": {"colors"},
        "act": {"colors"},
        "json": {"id", "name", "colors", "description", "source"},
        "csv": {"colors"},
        "brilliance-plt": {"colors"},
    }
    assert all(codec.info.can_import for codec in iter_codecs())
    assert {codec.info.id for codec in iter_codecs() if not codec.info.can_export} == {
        "brilliance-plt"
    }


def test_filesystem_service_import_export_reports_loss_and_refuses_overwrite(
    tmp_path: Path,
    palette: CustomPalette,
) -> None:
    output = tmp_path / "palette.gpl"
    exported = export_palette(palette, output, format_id="gpl")
    imported = import_palette(output)

    assert imported.palette.colors == palette.colors
    assert "description is not represented" in exported.report.messages
    assert "source/provenance is not represented" in exported.report.messages
    with pytest.raises(PaletteCodecError, match="already exists"):
        export_palette(palette, output, format_id="gpl")
