"""Tests for database module."""

import pytest

from database import game_exists, get_game_count, load_game, save_game
from model.board_game import BoardGame


@pytest.fixture
def sample_board_game(use_in_memory_db) -> BoardGame:
    """Create a minimal BoardGame for testing."""
    game = BoardGame(html_page_data=None, url="https://example.com/test-game", skip_html_parsing=True)
    game.parameters = {}
    game.name = "Test Game"
    game.final_price = "599"
    game.distributor = "Mindok"
    game.category = "Kostkové"
    game.min_players = 1
    game.max_players = 4
    game.play_time_minutes = 60
    game.bgg_rating = 7.5
    game.rate()
    return game


def test_game_exists_empty(use_in_memory_db) -> None:
    """game_exists returns False for empty DB."""
    assert game_exists("https://example.com/any") is False


def test_save_and_load_game(sample_board_game: BoardGame) -> None:
    """save_game and load_game roundtrip."""
    url = sample_board_game.url
    save_game(sample_board_game)
    assert game_exists(url) is True
    loaded = load_game(url)
    assert loaded is not None
    assert loaded.name == sample_board_game.name
    assert loaded.final_price == sample_board_game.final_price


def test_get_game_count(use_in_memory_db) -> None:
    """get_game_count returns correct count."""
    assert get_game_count() == 0
    game = BoardGame(html_page_data=None, url="https://example.com/g1", skip_html_parsing=True)
    game.parameters = {}
    game.name = "G1"
    game.rate()
    save_game(game)
    assert get_game_count() == 1
