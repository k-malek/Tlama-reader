"""Tests for search utils."""

from config import BASE_URL, FILTERS
from utils.search import normalize_game_url


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


def test_normalize_game_url_full_czech_path() -> None:
    url = f"{BASE_URL}/deskove-hry/brass-birmingham/"
    assert normalize_game_url(url) == url


def test_normalize_game_url_relative_path() -> None:
    assert normalize_game_url("/deskove-hry/brass-birmingham/") == f"{BASE_URL}/deskove-hry/brass-birmingham/"


def test_normalize_game_url_english_to_czech() -> None:
    url = f"{BASE_URL}/en/board-games/brass-birmingham/"
    assert normalize_game_url(url) == f"{BASE_URL}/deskove-hry/brass-birmingham/"


def test_normalize_game_url_rejects_empty() -> None:
    try:
        normalize_game_url("  ")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "empty" in str(e).lower()


def test_normalize_game_url_rejects_non_tlama() -> None:
    try:
        normalize_game_url("https://example.com/game")
        assert False, "Expected ValueError"
    except ValueError as e:
        assert "tlamagames.com" in str(e)


def test_category_and_mech_filters_exist() -> None:
    """Category and mechanic filters used in search exist."""
    from config import CATEGORY_FILTERS, MECHANIC_FILTERS

    for f in CATEGORY_FILTERS:
        assert f in FILTERS, f"Category filter {f} should be in FILTERS"
    for f in MECHANIC_FILTERS:
        assert f in FILTERS, f"Mechanic filter {f} should be in FILTERS"
