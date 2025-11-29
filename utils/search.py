from website_caller import WebsiteCaller
from bs4 import BeautifulSoup
from config import BASE_URL, ENDPOINTS, FILTERS
from model.board_game import BoardGame
from database import game_exists, save_game, load_game

def search_for_game(caller: WebsiteCaller, filters: list = None, pages: int = 1000, endpoint: str = "shop",
                    progress_callback=None) -> list:
    games_urls = []
    basic_filters = ["available", "games_only"]
    filters = basic_filters + (filters or [])
    mechanics="pv264="
    categories="pv258="
    query=""
    for filter in filters:
        if "cat:" in filter:
            categories += f"{FILTERS[filter.replace('cat:', '')]},"
        elif "mech:" in filter:
            mechanics += f"{FILTERS[filter.replace('mech:', '')]},"
        else:
            query += f"{FILTERS[filter]}&"
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
        print(url)
        html_resp = caller.get_text(url)
        soup = BeautifulSoup(html_resp, "html.parser")
        try:
            games = soup.find("div", id="products").find_all("div", class_="product")
        except AttributeError as e:
            print(f"No more pages: {e}")
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

def games_standings(games_urls: list, caller: WebsiteCaller, progress_callback=None, total_games=None):
    games = []
    total_games = total_games or len(games_urls)

    for idx, game_url in enumerate(games_urls, 1):
        full_url = f"{BASE_URL}{game_url}"
        print(full_url)

        if game_exists(full_url):
            # Always re-fetch game data to get latest price and other updated information
            # But preserve user-set boolean values (owned, has_demonic_vibe)
            existing_game = load_game(full_url)
            preserved_owned = getattr(existing_game, 'owned', False) if existing_game else False
            preserved_evil = getattr(existing_game, 'has_demonic_vibe', False) if existing_game else False

            game_data = caller.get_text(full_url)
            try:
                board_game = BoardGame(game_data, full_url)
                # Preserve the boolean values that users set
                board_game.owned = preserved_owned
                board_game.has_demonic_vibe = preserved_evil
            except ValueError as e:
                print(f"Error parsing game data: {e}")
                if progress_callback:
                    progress_callback(stage="games", current=idx, total=total_games,
                                     message=f"Fetching game {idx}/{total_games}...")
                continue
            save_game(board_game)
        else:
            game_data = caller.get_text(full_url)
            try:
                board_game = BoardGame(game_data, full_url)
            except ValueError as e:
                print(f"Error parsing game data: {e}")
                if progress_callback:
                    progress_callback(stage="games", current=idx, total=total_games,
                                     message=f"Fetching game {idx}/{total_games}...")
                continue
            board_game.rate()
            save_game(board_game)

        games.append(board_game)

        if progress_callback:
            progress_callback(stage="games", current=idx, total=total_games,
                             message=f"Fetching game {idx}/{total_games}...")

    games.sort(key=lambda x: x.my_rating, reverse=True)
    return games

def present_results(games: list):
    print("--------------------------------")
    print("# | Name | Price | Rating | URL")
    print("--------------------------------")
    for index, game in enumerate(games):
        print(f"{index + 1}. | {game.get_data_row()}")
    print("--------------------------------")
