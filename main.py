from website_caller import WebsiteCaller
from utils.promo import get_promo_game # type: ignore
from utils.search import search_for_game, present_results # type: ignore
from integrations.onesignal_caller import send_custom_event
from model.board_game import BoardGame

def main():
    caller = WebsiteCaller(timeout=30, use_browser=True)
    promo_game = get_promo_game(caller)
    print(promo_game.get_data_row())

    # games = search_for_game(caller, filters=["amazing", "cheap"])
    # present_results(games)

    # game_data = caller.get_text("https://www.tlamagames.com/deskove-hry/tiny-epic-crimes-en/")
    # board_game = BoardGame(game_data, "https://www.tlamagames.com/deskove-hry/tiny-epic-crimes-en/")
    # print(board_game.to_json())
    caller.close()

    if promo_game.my_rating > 100:
        send_custom_event(promo_game.to_json())

if __name__ == "__main__":
    main()
