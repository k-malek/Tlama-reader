"""Tests for BoardGame model."""

from model.board_game import BoardGame, RATING_PENALTY_DEMONIC


def test_from_html(sample_game_html: str) -> None:
    """BoardGame parses HTML and extracts attributes."""
    game = BoardGame(sample_game_html, "https://example.com/game")
    assert game.name == "Test Board Game"
    assert game.final_price == "899"
    assert game.distributor == "Mindok"
    assert game.image == "https://example.com/image.jpg"
    assert game.min_players == 1
    assert game.max_players == 4
    assert game.play_time_minutes == 45
    assert game.bgg_rating == 7.5
    assert game.complexity == 2.5
    assert "Kostkové" in (game.game_categories or [])
    assert "Solo / Solitaire Game" in (game.game_mechanics or [])


def test_rate_basic() -> None:
    """Rating is calculated from price, BGG, etc."""
    game = BoardGame(html_page_data=None, url="https://test.com", skip_html_parsing=True)
    game.parameters = {}
    game.final_price = "899"
    game.distributor = "Mindok"
    game.min_players = 1
    game.bgg_rating = 7.5
    game.play_time_minutes = 45
    game.game_categories = ["Kostkové"]
    game.game_mechanics = ["Solo / Solitaire Game"]
    game.rate()
    assert game.my_rating > 0


def test_rate_demonic_penalty() -> None:
    """Games with has_demonic_vibe get large penalty."""
    game = BoardGame(html_page_data=None, url="https://test.com", skip_html_parsing=True)
    game.parameters = {}
    game.final_price = "500"
    game.has_demonic_vibe = True
    game.rate()
    assert game.my_rating <= -RATING_PENALTY_DEMONIC


def test_from_db_row() -> None:
    """BoardGame.from_db_row creates instance from row-like dict."""
    row = {
        "url": "https://test.com/game",
        "name": "Test Game",
        "final_price": "999",
        "distributor": "Mindok",
        "category": "Kostkové",
        "weight_kg": 0.5,
        "ean": "123",
        "game_type": "Základní hra",
        "min_age": 10,
        "game_language": "Čeština",
        "rules_language": '["Čeština"]',
        "min_players": 1,
        "max_players": 4,
        "play_time_minutes": 60,
        "bgg_rating": 8.0,
        "complexity": 2.0,
        "author": "Author",
        "game_categories": '["Kostkové"]',
        "game_mechanics": '["Solo / Solitaire Game"]',
        "year_published": 2020,
        "artists": '["Artist"]',
        "has_demonic_vibe": 0,
        "owned": 0,
        "image": None,
    }
    game = BoardGame.from_db_row(row)
    assert game.url == "https://test.com/game"
    assert game.name == "Test Game"
    assert game.final_price == "999"
    assert game.min_players == 1
    assert game.my_rating is not None
