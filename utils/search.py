from website_caller import WebsiteCaller
from bs4 import BeautifulSoup
from config import BASE_URL
from model.board_game import BoardGame

FILTERS = {
    "available":"stock=1",
    "games_only":"pv117=2127",
    "for_one_player":"pv129=2142",
    "easy":"pv141=2409,14496,14553,13704,14583,14499,14613,13761,14193,14052,2367,14067,14352,14079,13746,6316",
    "hard":"pv141=6316,14217,14082,13596,14382,2205,13935,4898,13998,13644,4520,14394,15450,14325,14994,2271,15288,14334,16470,16482,18048,15717,4904,26046",
    # Categories, use "cat:dice_rolling"
    "solo":"13620",
    "dice_rolling":"13803",
    "modular_board":"13875"
}

def search_for_game(caller: WebsiteCaller, filters: list = None) -> list:
    basic_filters = ["available", "games_only"]
    filters = basic_filters + (filters or [])
    url = f"{BASE_URL}/deskove-hry/?"
    categories="pv264="
    for filter in filters:
        if "cat:" in filter:
            categories += f"{FILTERS[filter.replace('cat:', '')]},"
        else:
            url += f"{FILTERS[filter]}&"
    if categories != "pv264=":
        url += f"{categories[:-1]}&"
    url = url[:-1]
    print(url)
    html_resp = caller.get_text(url)
    soup = BeautifulSoup(html_resp, "html.parser")
    games = soup.find("div", id="products").find_all("div", class_="product")
    games_urls = [game.find("a").get("href") for game in games]
    games = games_standings(games_urls, caller)
    return games

def games_standings(games_urls: list, caller: WebsiteCaller):
    games = []
    for game_url in games_urls:
        print(f"{BASE_URL}{game_url}")
        game_data = caller.get_text(f"{BASE_URL}{game_url}")
        board_game = BoardGame(game_data)
        board_game.rate()
        games.append(board_game)
    games.sort(key=lambda x: x.my_rating, reverse=True)
    return games
