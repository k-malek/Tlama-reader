from website_caller import WebsiteCaller
from bs4 import BeautifulSoup
from config import BASE_URL, ENDPOINTS, FILTERS
from model.board_game import BoardGame
from database import game_exists, load_game, save_game

def search_for_game(caller: WebsiteCaller, filters: list = None, pages: int = 1000, endpoint: str = "shop") -> list:
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
    games = games_standings(games_urls, caller)
    return games

def games_standings(games_urls: list, caller: WebsiteCaller):
    games = []
    for game_url in games_urls:
        full_url = f"{BASE_URL}{game_url}"
        print(full_url)

        if game_exists(full_url):
            board_game = load_game(full_url)
            save_game(board_game)
        else:
            game_data = caller.get_text(full_url)
            try:
                board_game = BoardGame(game_data, full_url)
            except ValueError as e:
                print(f"Error parsing game data: {e}")
                continue
            board_game.rate()
            save_game(board_game)

        games.append(board_game)
    games.sort(key=lambda x: x.my_rating, reverse=True)
    return games

def present_results(games: list):
    print("--------------------------------")
    print("# | Name | Price | Rating | URL")
    print("--------------------------------")
    for index, game in enumerate(games):
        print(f"{index + 1}. | {game.get_data_row()}")
    print("--------------------------------")
