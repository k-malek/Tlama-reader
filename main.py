from website_caller import WebsiteCaller
from utils.promo import get_promo_game # type: ignore
from utils.search import search_for_game, present_results # type: ignore
from integrations.onesignal_caller import send_custom_event
from model.board_game import BoardGame
import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def run_promo_check():
    caller = WebsiteCaller(timeout=30, use_browser=True)
    try:
        promo_game = get_promo_game(caller)
    except Exception as e:
        logger.error(f"Error getting promo game: {e}")
        return
    logger.info(promo_game.get_data_row())
    caller.close()
    if promo_game.my_rating > 140:
        send_custom_event(promo_game.to_json())

def run_search_check(filters: list = None, endpoint: str = "shop"):
    caller = WebsiteCaller(timeout=30, use_browser=True)
    games = search_for_game(caller, filters=filters or [], endpoint=endpoint)
    present_results(games)
    caller.close()

def run_game_check(url: str):
    caller = WebsiteCaller(timeout=30, use_browser=True)
    game_data = caller.get_text(url)
    board_game = BoardGame(game_data, url)
    logger.info(board_game.print_all_info())
    caller.close()

if __name__ == "__main__":
    run_promo_check()
    #run_search_check(filters=["amazing"])
