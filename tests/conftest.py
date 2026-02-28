"""Pytest fixtures for Tlama caller tests."""

import pytest

from database import set_db_path


@pytest.fixture
def use_in_memory_db():
    """Use in-memory SQLite for database tests."""
    set_db_path(":memory:")
    yield
    set_db_path("games.db")


@pytest.fixture
def sample_game_html():
    """Minimal HTML that BoardGame.from_html can parse."""
    return """
    <html>
    <body>
        <h1>Test Board Game</h1>
        <span class="price-final-holder">899 Kč</span>
        <a data-testid="productCardBrandName"><span>Mindok</span></a>
        <a class="highlighted" href="https://example.com/image.jpg"></a>
        <div class="extended-description">
            <table class="detail-parameters">
                <tr><th>5. Minimální počet hráčů</th><td>1</td></tr>
                <tr><th>6. Maximální počet hráčů</th><td>4</td></tr>
                <tr><th>7. Herní doba (minut)</th><td>45</td></tr>
                <tr><th>8. Hodnocení Boardgamegeek (0-10)</th><td>7.5</td></tr>
                <tr><th>9. Náročnost (1-5)</th><td>2.5</td></tr>
                <tr><th>Herní kategorie</th><td>Kostkové, Karetní</td></tr>
                <tr><th>Herní mechaniky</th><td>Solo / Solitaire Game</td></tr>
            </table>
        </div>
    </body>
    </html>
    """
