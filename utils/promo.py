from website_caller import WebsiteCaller
from model.board_game import BoardGame
from bs4 import BeautifulSoup
from config import BASE_URL
from database import game_exists, load_game, save_game


def get_promo_game_url(caller: WebsiteCaller) -> str:
    """Get the URL of the current promo game from tlamagames.com homepage."""
    html_resp = caller.get_html_with_browser(
        url=f"{BASE_URL}/",
        wait_for_selector="#fvStudio-component-topproduct",
        wait_until="load")
    soup = BeautifulSoup(html_resp, "html.parser")
    promo_div = soup.find("div", id="fvStudio-component-topproduct")
    href = promo_div.find("a").get("href")
    # Make sure it's a full URL
    if href and not href.startswith("http"):
        href = f"{BASE_URL}{href}"
    return href


def get_promo_game(caller: WebsiteCaller) -> BoardGame:
    """Get the full BoardGame object for the current promo game."""
    url = get_promo_game_url(caller)

    # Check if game exists in database
    if game_exists(url):
        return load_game(url)

    # Fetch from website
    game_data = caller.get_text(url)
    board_game = BoardGame(game_data, url)
    board_game.rate()

    # Save to database
    save_game(board_game)

    return board_game

