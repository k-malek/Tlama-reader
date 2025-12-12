from website_caller import WebsiteCaller
from utils.promo import get_promo_game # type: ignore
from utils.search import search_for_game, present_results # type: ignore
from integrations.onesignal_caller import send_custom_event
from model.board_game import BoardGame
from ui.interface import run_interface
import logging
import sys

# Configure root logger so all child loggers inherit the configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def run_promo_check():
    caller = WebsiteCaller(timeout=30, use_browser=True)
    try:
        promo_game = get_promo_game(caller)
    except Exception as e:
        logger.error(f"Error getting promo game: {e}")
        return
    logger.info(promo_game.get_data_row())
    if promo_game.my_rating > 140:
        send_custom_event(promo_game.to_json())
    caller.close()

def run_best_deals_check():
    caller = WebsiteCaller(timeout=30, use_browser=True)
    games = search_for_game(caller, filters=["discounted"])
    # Filter out owned games
    games = [game for game in games if not getattr(game, 'owned', False)]
    if not games:
        logger.info("No unowned discounted games found")
        caller.close()
        return
    best_deal_game = games[0]
    best_deal_game.deal = "weekly"
    logger.info(best_deal_game.get_data_row())
    send_custom_event(best_deal_game.to_json())
    caller.close()

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
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "promo":
            run_promo_check()
        elif command == "best-deals":
            run_best_deals_check()
        elif command == "search":
            filters = sys.argv[2:] if len(sys.argv) > 2 else None
            run_search_check(filters=filters)
        elif command == "game" and len(sys.argv) > 2:
            run_game_check(sys.argv[2])
        elif command == "interface":
            run_interface()
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: promo, best-deals, search, game, interface")
    else:
        # Default behavior for backward compatibility
        run_best_deals_check()
