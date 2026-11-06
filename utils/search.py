import logging
from typing import Callable, Optional

from bs4 import BeautifulSoup

from config import BASE_URL, ENDPOINTS, FILTERS, to_czk_game_url
from database import game_exists, load_game, save_game
from model.board_game import BoardGame
from website_caller import WebsiteCaller

logger = logging.getLogger(__name__)


def normalize_game_url(url: str) -> str:
    """Normalize a Tlama Games product URL to a full Czech (CZK) URL."""
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
    url = to_czk_game_url(url)
    if url.startswith("/"):
        url = f"{BASE_URL}{url}"
    elif not url.startswith("http"):
        raise ValueError("Invalid game URL")
    if "tlamagames.com" not in url:
        raise ValueError("URL must be from tlamagames.com")
    return url


def fetch_and_save_game(url: str, caller: WebsiteCaller) -> BoardGame:
    """Fetch a single game page, rate it, and save to the database."""
    full_url = normalize_game_url(url)

    preserved_owned = False
    preserved_evil = False
    if game_exists(full_url):
        existing_game = load_game(full_url)
        if existing_game:
            preserved_owned = getattr(existing_game, "owned", False)
            preserved_evil = getattr(existing_game, "has_demonic_vibe", False)

    game_data = caller.get_text(full_url)
    try:
        board_game = BoardGame(game_data, full_url)
    except ValueError as e:
        raise ValueError(f"Could not parse game page: {e}") from e

    board_game.owned = preserved_owned
    board_game.has_demonic_vibe = preserved_evil
    save_game(board_game)
    return board_game


def search_for_game(
    caller: WebsiteCaller,
    filters: Optional[list[str]] = None,
    pages: int = 1000,
    endpoint: str = "shop",
    progress_callback: Optional[Callable[..., None]] = None,
) -> list[BoardGame]:
    games_urls = []
    basic_filters = ["available", "games_only"]
    filters = basic_filters + (filters or [])
    mechanics="pv264="
    categories="pv258="
    query=""
    for filter_name in filters:
        if "cat:" in filter_name:
            key = filter_name.replace("cat:", "")
            if key not in FILTERS:
                raise KeyError(f"Unknown category filter: {filter_name}")
            categories += f"{FILTERS[key]},"
        elif "mech:" in filter_name:
            key = filter_name.replace("mech:", "")
            if key not in FILTERS:
                raise KeyError(f"Unknown mechanic filter: {filter_name}")
            mechanics += f"{FILTERS[key]},"
        else:
            if filter_name not in FILTERS:
                raise KeyError(f"Unknown filter: {filter_name}")
            query += f"{FILTERS[filter_name]}&"
    if categories != "pv258=":
        query += f"{categories[:-1]}&"
    if mechanics != "pv264=":
        query += f"{mechanics[:-1]}&"
    query = query[:-1]

    # Stage 1: Fetch pages
    total_pages = 0
    for i in range(1, pages + 1):
        url = f"{BASE_URL}{ENDPOINTS[endpoint]}strana-{i}/?"
        url += query
        logger.debug("Fetching page URL: %s", url)
        html_resp = caller.get_text(url)
        soup = BeautifulSoup(html_resp, "html.parser")
        try:
            games = soup.find("div", id="products").find_all("div", class_="product")
        except AttributeError as e:
            logger.debug("No more pages: %s", e)
            break
        games_urls.extend([game.find("a").get("href") for game in games])
        total_pages = i
        if progress_callback:
            progress_callback(stage="pages", current=i, total=None, message=f"Fetching page {i}...")

    # After stage 1, we know how many games to fetch
    total_games = len(games_urls)
    if progress_callback:
        progress_callback(stage="pages_complete", current=total_pages, total=total_pages,
                         message=f"Found {total_games} games. Starting to fetch game data...")

    games = games_standings(games_urls, caller, progress_callback=progress_callback, total_games=total_games)
    return games

def games_standings(
    games_urls: list[str],
    caller: WebsiteCaller,
    progress_callback: Optional[Callable[..., None]] = None,
    total_games: Optional[int] = None,
) -> list[BoardGame]:
    games = []
    total_games = total_games or len(games_urls)

    for idx, game_url in enumerate(games_urls, 1):
        full_url = f"{BASE_URL}{game_url}"
        logger.debug("Fetching game: %s", full_url)

        try:
            board_game = fetch_and_save_game(full_url, caller)
        except ValueError as e:
            logger.warning("Error fetching game %s: %s", full_url, e)
            if progress_callback:
                progress_callback(stage="games", current=idx, total=total_games,
                                 message=f"Fetching game {idx}/{total_games}...")
            continue

        games.append(board_game)

        if progress_callback:
            progress_callback(stage="games", current=idx, total=total_games,
                             message=f"Fetching game {idx}/{total_games}...")

    games.sort(key=lambda x: x.my_rating, reverse=True)
    return games

def present_results(games: list[BoardGame]) -> None:
    """Print search results to stdout (CLI output)."""
    print("--------------------------------")
    print("# | Name | Price | Rating | URL")
    print("--------------------------------")
    for index, game in enumerate(games):
        print(f"{index + 1}. | {game.get_data_row()}")
    print("--------------------------------")
