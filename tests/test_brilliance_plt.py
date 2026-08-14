from __future__ import annotations

from pathlib import Path

import pytest

from retropal.cli import main
from retropal.palettes.interchange import PaletteCodecError, get_codec
from retropal.palettes.interchange.registry import codec_for_export, identify_codec
from retropal.palettes.interchange.service import import_palette
from retropal.palettes.native import load_native_palette
from tests.brilliance_fixtures import brilliance_palette
from tests.ilbm_fixtures import iff_chunk, ilbm_form


def _colors() -> tuple[tuple[int, int, int], ...]:
    return (
        (0, 0, 0),
        (255, 0, 128),
        (0, 0, 0),
        (1, 2, 3),
    ) + tuple((index, index, index) for index in range(4, 256))


@pytest.mark.parametrize("version", ["1.0", "2.0"])
def test_verified_brilliance_versions_import_256_ordered_registers(version: str) -> None:
    colors = _colors()
    result = get_codec("brilliance-plt").decode(
        brilliance_palette(colors, version=version),
        palette_id="brilliance",
        fallback_name="Brilliance",
    )

    assert result.palette.colors == colors
    assert len(result.palette.colors) == 256
    assert result.palette.colors[0] == result.palette.colors[2]
    assert result.palette.colors[3] == (1, 2, 3)
    assert f"Brilliance {version}" in (result.palette.source or "")
    assert any("all 256" in message for message in result.report.messages)
    assert any("128 Brilliance gradient slots" in message for message in result.report.messages)


def test_gradient_slots_and_range_chunks_are_reported_not_imported() -> None:
    gradients = tuple((255, 17, 34) for _ in range(128))
    result = get_codec("brilliance-plt").decode(
        brilliance_palette(
            _colors(),
            gradients=gradients,
            extra_chunks=(iff_chunk(b"DRNG", b"documented elsewhere"),),
        ),
        palette_id="ranges",
        fallback_name="Ranges",
    )

    assert len(result.palette.colors) == 256
    assert (255, 17, 34) not in result.palette.colors
    assert any("DRNG" in message for message in result.report.messages)


def test_pre_aga_precision_is_reported_without_channel_normalization() -> None:
    colors = tuple((index % 16 * 17,) * 3 for index in range(256))
    result = get_codec("brilliance-plt").decode(
        brilliance_palette(colors), palette_id="ocs", fallback_name="OCS"
    )

    assert result.palette.colors == colors
    assert any("4-bit-expanded" in message for message in result.report.messages)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"not an iff", "Malformed"),
        (
            ilbm_form(
                iff_chunk(b"ANNO", b"Not Brilliance"),
                iff_chunk(b"CMAP", bytes(384 * 3)),
            ),
            "ANNO signature",
        ),
        (
            ilbm_form(
                iff_chunk(b"ANNO", b"Written by Brilliance 1.0"),
                iff_chunk(b"CMAP", bytes(383 * 3)),
            ),
            "exactly 384",
        ),
        (
            brilliance_palette(_colors(), extra_chunks=(iff_chunk(b"XXXX", b"unknown"),)),
            "Unsupported Brilliance palette chunks",
        ),
    ],
)
def test_malformed_or_unsupported_brilliance_input_is_controlled(data: bytes, message: str) -> None:
    with pytest.raises(PaletteCodecError, match=message):
        get_codec("brilliance-plt").decode(data, palette_id="bad", fallback_name="Bad")


def test_signature_sniffing_distinguishes_brilliance_from_generic_ilbm(tmp_path: Path) -> None:
    codec = get_codec("brilliance-plt")
    data = brilliance_palette(_colors())
    assert codec.sniff(data)
    assert not codec.sniff(ilbm_form(iff_chunk(b"BMHD", bytes(20)), iff_chunk(b"CMAP", bytes(3))))
    assert identify_codec(tmp_path / "palette.plt", data).info.id == "brilliance-plt"


def test_brilliance_export_is_honestly_unsupported(tmp_path: Path) -> None:
    codec = get_codec("brilliance-plt")
    assert codec.info.can_import
    assert not codec.info.can_export
    with pytest.raises(PaletteCodecError, match="gradient serialization is undocumented"):
        codec.encode(
            codec.decode(
                brilliance_palette(_colors()),
                palette_id="p",
                fallback_name="P",
            ).palette
        )
    with pytest.raises(PaletteCodecError, match="export is not supported"):
        codec_for_export(tmp_path / "palette.plt", "brilliance-plt")


def test_cli_import_saves_normal_native_palette(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "Historical Palette.plt"
    source.write_bytes(brilliance_palette(_colors(), version="1.0"))
    store = tmp_path / "store"

    assert (
        main(
            [
                "custom-palettes",
                "--store",
                str(store),
                "import",
                str(source),
                "--format",
                "brilliance-plt",
            ]
        )
        == 0
    )
    palette = load_native_palette(next(store.glob("*.retropal-palette.json")))
    assert palette.colors == _colors()
    output = capsys.readouterr().out
    assert "128 Brilliance gradient slots" in output
    assert "4-bit-expanded" not in output


def test_import_service_uses_strong_brilliance_sniff(tmp_path: Path) -> None:
    source = tmp_path / "palette.plt"
    source.write_bytes(brilliance_palette(_colors()))
    assert import_palette(source).palette.colors == _colors()
