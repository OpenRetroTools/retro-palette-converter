import json

from PIL import Image

from retropal.core.palette_export import (
    amiga_ocs_word,
    export_gpl,
    export_json,
    palette_for_result,
    used_colors,
)


def test_used_colors_ignores_transparent_pixels() -> None:
    image = Image.new("RGBA", (3, 1))
    image.putdata([(1, 2, 3, 255), (1, 2, 3, 255), (9, 8, 7, 0)])
    assert used_colors(image) == ((1, 2, 3),)


def test_palette_for_result_uses_declared_order() -> None:
    source = Image.new("RGBA", (1, 1), (0, 0, 0, 255))
    converted = Image.new("RGBA", (2, 1))
    converted.putdata([(155, 188, 15, 255), (15, 56, 15, 255)])
    assert palette_for_result(source, converted, "gameboy") == (
        (15, 56, 15),
        (155, 188, 15),
    )


def test_amiga_ocs_word() -> None:
    assert amiga_ocs_word((255, 170, 0)) == "$FA0"


def test_export_gpl(tmp_path) -> None:
    output = export_gpl(tmp_path / "test.gpl", "Example", ((1, 2, 3),))
    text = output.read_text(encoding="utf-8")
    assert text.startswith("GIMP Palette\nName: Example")
    assert "  1   2   3" in text


def test_export_json_includes_amiga_metadata(tmp_path) -> None:
    output = export_json(
        tmp_path / "test.json",
        "amiga-ocs-16",
        ((255, 170, 0),),
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["color_count"] == 1
    assert payload["amiga_ocs_words"] == ["$FA0"]
