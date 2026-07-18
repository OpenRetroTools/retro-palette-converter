from __future__ import annotations

import pytest

from retropal.gui.compare_dialog import (
    DEFAULT_COMPARE_IDS,
    MAX_COMPARE_ALGORITHMS,
    selected_compare_ids,
)


def test_default_compare_algorithms_are_available() -> None:
    assert selected_compare_ids(DEFAULT_COMPARE_IDS) == DEFAULT_COMPARE_IDS


def test_compare_selection_preserves_registry_order() -> None:
    assert selected_compare_ids(("sierra", "none", "atkinson")) == (
        "none",
        "atkinson",
        "sierra",
    )


def test_compare_requires_at_least_one_algorithm() -> None:
    with pytest.raises(ValueError, match="at least one"):
        selected_compare_ids(())


def test_compare_limits_number_of_algorithms() -> None:
    from retropal.core.dither import list_dithers

    too_many = list_dithers()[: MAX_COMPARE_ALGORITHMS + 1]
    with pytest.raises(ValueError, match="at most"):
        selected_compare_ids(too_many)
