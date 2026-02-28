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


def test_rate_cheaper_beats_higher_discount() -> None:
    """Cheaper option ranks higher than more expensive with higher % off (same game)."""
    cheap = BoardGame(html_page_data=None, url="https://tlamagames.com/deskove-hry/ark-nova/", skip_html_parsing=True)
    cheap.parameters = {}
    cheap.final_price = "1499"
    cheap.discount_percent = 10
    cheap.distributor = "Feuerland Spiele"
    cheap.bgg_rating = 8.5
    cheap.rate()

    expensive = BoardGame(html_page_data=None, url="https://tlamagames.com/deskove-hry/archa-nova/", skip_html_parsing=True)
    expensive.parameters = {}
    expensive.final_price = "1629"
    expensive.discount_percent = 18
    expensive.distributor = "Mindok"
    expensive.bgg_rating = 8.5
    expensive.rate()

    assert cheap.my_rating > expensive.my_rating


def test_rate_cheaper_beats_subtle_discount_nucleum() -> None:
    """Cheaper Nucleum CZ (1449, 9%) beats EN (1499, 11%)."""
    cheap = BoardGame(html_page_data=None, url="https://tlamagames.com/deskove-hry/nukleum--cesky/", skip_html_parsing=True)
    cheap.parameters = {}
    cheap.final_price = "1449"
    cheap.discount_percent = 9
    cheap.distributor = "Old Dawg"
    cheap.bgg_rating = 8.1
    cheap.rate()

    expensive = BoardGame(html_page_data=None, url="https://tlamagames.com/deskove-hry/nucleum/", skip_html_parsing=True)
    expensive.parameters = {}
    expensive.final_price = "1499"
    expensive.discount_percent = 11
    expensive.distributor = "Board&Dice"
    expensive.bgg_rating = 8.1
    expensive.rate()

    assert cheap.my_rating > expensive.my_rating


def test_rate_discount_bonus() -> None:
    """Games with discount get rating bonus."""
    game = BoardGame(html_page_data=None, url="https://test.com", skip_html_parsing=True)
    game.parameters = {}
    game.final_price = "1799"
    game.discount_percent = 10
    game.distributor = "Mindok"
    game.min_players = 2
    game.bgg_rating = 8.0
    game.rate()
    # Discount 10% gives +1 (1 per 10%)
    assert game.my_rating > 0
    game_no_discount = BoardGame(html_page_data=None, url="https://test.com", skip_html_parsing=True)
    game_no_discount.parameters = {}
    game_no_discount.final_price = "1799"
    game_no_discount.distributor = "Mindok"
    game_no_discount.min_players = 2
    game_no_discount.bgg_rating = 8.0
    game_no_discount.rate()
    assert game.my_rating > game_no_discount.my_rating


def test_rate_demonic_penalty() -> None:
    """Games with has_demonic_vibe get large penalty."""
    game = BoardGame(html_page_data=None, url="https://test.com", skip_html_parsing=True)
    game.parameters = {}
    game.final_price = "500"
    game.has_demonic_vibe = True
    game.rate()
    assert game.my_rating <= -RATING_PENALTY_DEMONIC


def test_from_html_with_discount(sample_game_html_with_discount: str) -> None:
    """BoardGame parses discounted price block."""
    game = BoardGame(sample_game_html_with_discount, "https://example.com/game")
    assert game.original_price == "1999"
    assert game.final_price == "1799"
    assert game.discount_percent == 10


def test_rate_high_bgg_substantial_game() -> None:
    """High BGG + complexity (e.g. Andromeda-like) gets ~350."""
    game = BoardGame(html_page_data=None, url="https://test.com", skip_html_parsing=True)
    game.parameters = {}
    game.final_price = "1799"
    game.discount_percent = 10
    game.distributor = "Mindok"
    game.min_players = 2
    game.bgg_rating = 8.3
    game.complexity = 3.7
    game.play_time_minutes = 160
    game.game_categories = ["Průzkum vesmíru", "Sci-fi"]
    game.game_mechanics = ["Dice Rolling", "Hand Management", "Variable Player Powers"]
    game.rate()
    assert 320 <= game.my_rating <= 380


def test_rate_moderate_bgg_light_game() -> None:
    """Moderate BGG + many tags (e.g. Dračí hrad-like) gets ~150."""
    game = BoardGame(html_page_data=None, url="https://test.com", skip_html_parsing=True)
    game.parameters = {}
    game.final_price = "599"
    game.discount_percent = 40
    game.distributor = "Dino"
    game.min_players = 1
    game.bgg_rating = 7.3
    game.complexity = 2.0
    game.play_time_minutes = 75
    game.game_categories = ["Kostkové", "Bludiště", "Dobrodružné", "Fantasy"]
    game.game_mechanics = ["Cooperative Game", "Dice Rolling", "Modular Board", "Hand Management"]
    game.rate()
    assert 130 <= game.my_rating <= 170


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
