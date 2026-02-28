import argparse
import logging
import sys

from config import MIN_RATING_FOR_NOTIFICATION
from database import get_excluded_game_urls
from integrations.onesignal_caller import send_custom_event
from model.board_game import BoardGame
from ui.interface import run_interface
from utils.blocklist import get_blocklist_path, is_url_excluded
from utils.promo import get_promo_game
from utils.search import present_results, search_for_game
from website_caller import WebsiteCaller

# Configure root logger so all child loggers inherit the configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def run_promo_check() -> None:
    with WebsiteCaller(timeout=30, use_browser=True) as caller:
        try:
            promo_game = get_promo_game(caller)
            logger.info(promo_game.get_data_row())
            if is_url_excluded(promo_game.url):
                logger.info("Skipping excluded game: %s", promo_game.url)
                return
            if promo_game.my_rating > MIN_RATING_FOR_NOTIFICATION:
                send_custom_event(promo_game.to_json())
        except Exception as e:
            logger.error("Error getting promo game: %s", e)


def run_best_deals_check() -> None:
    with WebsiteCaller(timeout=30, use_browser=True) as caller:
        games = search_for_game(caller, filters=["discounted"])
        # Filter out owned and excluded games
        games = [
            game
            for game in games
            if not getattr(game, "owned", False)
            and not getattr(game, "has_demonic_vibe", False)
            and not is_url_excluded(game.url)
        ]
        if not games:
            logger.info("No unowned discounted games found")
            return
        best_deal_game = games[0]
        best_deal_game.deal = "weekly"
        logger.info(best_deal_game.get_data_row())
        send_custom_event(best_deal_game.to_json())


def run_search_check(filters: list | None = None, endpoint: str = "shop") -> None:
    with WebsiteCaller(timeout=30, use_browser=True) as caller:
        games = search_for_game(caller, filters=filters or [], endpoint=endpoint)
        present_results(games)


def run_game_check(url: str) -> None:
    with WebsiteCaller(timeout=30, use_browser=True) as caller:
        game_data = caller.get_text(url)
        board_game = BoardGame(game_data, url)
        board_game.print_all_info()


def run_export_excluded() -> None:
    """Export URLs of owned/evil games from DB to blocklist file."""
    urls = get_excluded_game_urls()
    path = get_blocklist_path()
    header = (
        "# Excluded game URLs - never send notifications for these games\n"
        "# One URL per line. Add via: uv run python main.py export-excluded\n"
        "# Or edit manually. Used by CI and local runs.\n\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(header)
        for url in sorted(urls):
            f.write(f"{url}\n")
    logger.info("Exported %d URLs to %s", len(urls), path)


def main() -> None:
    """Parse CLI arguments and run the appropriate command."""
    parser = argparse.ArgumentParser(
        description="Tlama Games deal finder - check board game promos and search for deals."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("promo", help="Check daily promo game")
    subparsers.add_parser("best-deals", help="Check weekly best discounted deals")
    subparsers.add_parser("interface", help="Launch GUI")
    subparsers.add_parser(
        "export-excluded",
        help="Export owned/evil game URLs from DB to blocklist file",
    )

    search_parser = subparsers.add_parser("search", help="Search games with filters")
    search_parser.add_argument("filters", nargs="*", help="Filter names (e.g. discounted, cheap)")

    game_parser = subparsers.add_parser("game", help="Check a specific game by URL")
    game_parser.add_argument("url", help="Game page URL")

    args = parser.parse_args()
    command = args.command

    if command == "promo":
        run_promo_check()
    elif command == "best-deals":
        run_best_deals_check()
    elif command == "search":
        run_search_check(filters=args.filters if args.filters else None)
    elif command == "game":
        run_game_check(args.url)
    elif command == "interface":
        run_interface()
    elif command == "export-excluded":
        run_export_excluded()
    elif command is None:
        run_best_deals_check()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
