"""Tests for search utils."""

from config import FILTERS


def test_filters_available() -> None:
    """Basic filters exist in FILTERS."""
    assert "available" in FILTERS
    assert "games_only" in FILTERS
    assert "discounted" in FILTERS


def test_filter_values_valid() -> None:
    """Filter values are non-empty strings."""
    for key, value in FILTERS.items():
        assert isinstance(value, str), f"Filter {key} value should be str"
        assert len(value) > 0, f"Filter {key} value should not be empty"


def test_category_and_mech_filters_exist() -> None:
    """Category and mechanic filters used in search exist."""
    from config import CATEGORY_FILTERS, MECHANIC_FILTERS

    for f in CATEGORY_FILTERS:
        assert f in FILTERS, f"Category filter {f} should be in FILTERS"
    for f in MECHANIC_FILTERS:
        assert f in FILTERS, f"Mechanic filter {f} should be in FILTERS"
