from website_caller import WebsiteCaller
from utils import search_for_game


def main():
    # Use browser automation to execute JavaScript and wait for dynamic content
    caller = WebsiteCaller(timeout=30, use_browser=True)
    try:
        games = search_for_game(caller,["cat:solo","cat:dice_rolling","cat:modular_board"])
        for game in games:
            print(game.name, game.final_price+" Kč", game.my_rating)
    except Exception as e:
        raise e
    finally:
        caller.close()

if __name__ == "__main__":
    main()
