"""Synthetic Brilliance structures derived from the documented historical corpus."""

from __future__ import annotations

from tests.ilbm_fixtures import iff_chunk, ilbm_form


def brilliance_palette(
    colors: tuple[tuple[int, int, int], ...],
    *,
    gradients: tuple[tuple[int, int, int], ...] | None = None,
    version: str = "2.0",
    extra_chunks: tuple[bytes, ...] = (),
) -> bytes:
    if len(colors) != 256:
        raise ValueError("Brilliance fixture requires 256 register slots")
    gradient_colors = gradients or tuple((0, 0, 0) for _ in range(128))
    if len(gradient_colors) != 128:
        raise ValueError("Brilliance fixture requires 128 gradient slots")
    annotation = (
        b"Written by Brilliance 1.0" if version == "1.0" else b"Written by Brilliance Release 2.0 "
    )
    cmap = bytes(channel for color in (*colors, *gradient_colors) for channel in color)
    return ilbm_form(iff_chunk(b"ANNO", annotation), iff_chunk(b"CMAP", cmap), *extra_chunks)
