"""Conversion state and orchestration for the desktop interface."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from retropal.core.converter import convert
from retropal.core.image_io import load_image, save_png
from retropal.core.models import DitherMode
from retropal.core.palette_export import (
    amiga_ocs_word,
    export_gpl,
    export_json,
    palette_for_result,
)
from retropal.palettes import get_palette_info, palette_colors
from retropal.palettes.base import RGBColor


def resolve_display_palette_colors(
    palette_id: str,
    source_image: Image.Image,
) -> tuple[RGBColor, ...]:
    """Resolve the complete palette that should be shown for a source image."""
    return palette_colors(palette_id, source_image)


def palette_display_metadata(palette_id: str, colors: tuple[RGBColor, ...]) -> str:
    """Describe displayed colors using palette registry metadata."""
    metadata = f"Palette colors: {len(colors)}"
    if "ocs" in get_palette_info(palette_id).tags:
        words = " ".join(amiga_ocs_word(color) for color in colors)
        metadata += f" · OCS 12-bit RGB\n{words}"
    return metadata


class ConverterController:
    """Keep image conversion state independent from Qt widgets."""

    def __init__(self) -> None:
        self.source_path: Path | None = None
        self.source_image: Image.Image | None = None
        self.converted_image: Image.Image | None = None
        self.palette_id = "amiga-ocs-32"
        self.dither = DitherMode.NONE
        self.result_palette: tuple[tuple[int, int, int], ...] = ()
        self.display_palette: tuple[RGBColor, ...] = ()

    @property
    def has_image(self) -> bool:
        return self.source_image is not None

    def load(self, path: Path) -> Image.Image:
        self.source_path = path
        self.source_image = load_image(path)
        self.converted_image = None
        self.result_palette = ()
        self.display_palette = ()
        return self.source_image

    def set_options(self, palette_id: str, dither: str | DitherMode) -> None:
        self.palette_id = palette_id
        self.dither = dither

    def refresh(self) -> Image.Image:
        if self.source_image is None:
            raise RuntimeError("No source image loaded")
        self.display_palette = resolve_display_palette_colors(
            self.palette_id,
            self.source_image,
        )
        self.converted_image = convert(
            self.source_image,
            self.palette_id,
            self.dither,
        )
        self.result_palette = palette_for_result(
            self.source_image,
            self.converted_image,
            self.palette_id,
        )
        return self.converted_image

    def suggested_output_path(self) -> Path:
        if self.source_path is None:
            raise RuntimeError("No source image loaded")
        return self.source_path.with_name(f"{self.source_path.stem}-{self.palette_id}.png")

    def export(self, path: Path) -> Path:
        if self.converted_image is None:
            raise RuntimeError("No converted image available")
        output = path if path.suffix.lower() == ".png" else path.with_suffix(".png")
        save_png(self.converted_image, output)
        return output

    def export_palette(self, path: Path) -> Path:
        """Export the current result palette as GPL or JSON."""
        if not self.result_palette:
            raise RuntimeError("No converted palette available")
        suffix = path.suffix.lower()
        if suffix == ".gpl":
            return export_gpl(path, self.palette_id, self.result_palette)
        if suffix == ".json":
            return export_json(path, self.palette_id, self.result_palette)
        raise ValueError("Palette export must use .gpl or .json")
