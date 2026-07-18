from retropal.core.models import DitherMode, ImageInfo


def test_image_info_is_immutable() -> None:
    info = ImageInfo(
        width=320,
        height=256,
        mode="RGBA",
        unique_rgb_colors=12,
        has_alpha=True,
    )
    assert info.width == 320
    assert info.height == 256
    assert info.mode == "RGBA"
    assert info.unique_rgb_colors == 12
    assert info.has_alpha is True


def test_dither_mode_values() -> None:
    assert DitherMode.NONE.value == "none"
    assert DitherMode.FLOYD_STEINBERG.value == "floyd-steinberg"
    assert DitherMode.ATKINSON.value == "atkinson"
    assert DitherMode.BAYER_2X2.value == "bayer-2x2"
    assert DitherMode.BAYER_4X4.value == "bayer-4x4"
    assert DitherMode.BAYER_8X8.value == "bayer-8x8"
