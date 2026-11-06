import logging

from bs4 import BeautifulSoup

from config import BASE_URL
from model.board_game import BoardGame
from utils.search import fetch_and_save_game
from website_caller import WebsiteCaller

logger = logging.getLogger(__name__)


def get_promo_game_url(caller: WebsiteCaller) -> str:
    """Get the URL of the current promo game from tlamagames.com homepage."""
    logger.debug("Fetching promo game URL from homepage")
    html_resp = caller.get_html_with_browser(
        url=f"{BASE_URL}/",
        wait_for_selector="#fvStudio-component-topproduct",
        wait_until="load")
    logger.debug("Homepage HTML fetched, parsing for promo game")
    soup = BeautifulSoup(html_resp, "html.parser")
    promo_div = soup.find("div", id="fvStudio-component-topproduct")
    href = promo_div.find_all("a")[-1].get("href")
    # Make sure it's a full URL
    if href and not href.startswith("http"):
        href = f"{BASE_URL}{href}"
    logger.debug(f"Promo game URL found: {href}")
    return href


def get_promo_game(caller: WebsiteCaller) -> BoardGame:
    """Get the current promo game, always re-reading its product page.

    A saved row is not reused. Daily promo prices change, and an older row
    would keep yesterday's price and omit the crossed-out original price.
    """
    url = get_promo_game_url(caller)
    logger.debug("Refreshing promo game from website: %s", url)
    board_game = fetch_and_save_game(url, caller)
    logger.debug(
        "Promo game ready: %s | %s Kč (original %s Kč, −%s%%)",
        board_game.name,
        board_game.final_price,
        board_game.original_price,
        board_game.discount_percent,
    )
    return board_game

