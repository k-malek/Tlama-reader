from website_caller import WebsiteCaller
from model.board_game import BoardGame
from bs4 import BeautifulSoup
from config import BASE_URL
from database import game_exists, load_game, save_game
import logging

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
    """Get the full BoardGame object for the current promo game."""
    logger.debug("Starting to get promo game")
    url = get_promo_game_url(caller)
    logger.debug(f"Checking if game exists in database: {url}")

    # Check if game exists in database
    if game_exists(url):
        logger.debug("Game found in database, loading from database")
        board_game = load_game(url)
        # If image is missing (old games saved before image column), re-fetch to populate it
        if not board_game.image:
            logger.debug("Game image missing, re-fetching game data to populate image")
            game_data = caller.get_text(url)
            board_game = BoardGame(game_data, url)
            save_game(board_game)
            logger.debug("Game data re-fetched and saved with image")
        else:
            logger.debug(f"Game loaded from database: {board_game.name} (Rating: {board_game.my_rating})")
        return board_game

    # Fetch from website
    logger.debug("Game not in database, fetching from website")
    game_data = caller.get_text(url)
    board_game = BoardGame(game_data, url)
    logger.debug(f"Game data parsed: {board_game.name} (Rating: {board_game.my_rating})")

    # Save to database
    logger.debug("Saving game to database")
    save_game(board_game)
    logger.debug("Game saved to database successfully")

    return board_game

