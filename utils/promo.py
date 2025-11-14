from website_caller import WebsiteCaller
from model.board_game import BoardGame
from bs4 import BeautifulSoup
from config import BASE_URL


def get_promo_game_url(caller: WebsiteCaller) -> str:
    """Get the URL of the current promo game from tlamagames.com homepage."""
    html_resp = caller.get_html_with_browser(
        url=f"{BASE_URL}/",
        wait_for_selector="#fvStudio-component-topproduct",
        wait_until="load")
    soup = BeautifulSoup(html_resp, "html.parser")
    promo_div = soup.find("div", id="fvStudio-component-topproduct")
    return promo_div.find("a").get("href")


def get_promo_game(caller: WebsiteCaller) -> BoardGame:
    """Get the full BoardGame object for the current promo game."""
    url = get_promo_game_url(caller)
    game_data = caller.get_text(url)
    board_game = BoardGame(game_data)
    board_game.rate()
    return board_game

