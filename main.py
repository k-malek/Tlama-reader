from website_caller import WebsiteCaller
from utils.promo import get_promo_game # type: ignore
from utils.search import search_for_game, present_results # type: ignore
from integrations.onesignal_caller import create_notification

def main():
    # caller = WebsiteCaller(timeout=30, use_browser=True)
    # promo_game = get_promo_game(caller)
    # print(promo_game.get_data_row())

    # games = search_for_game(caller, filters=["cat:animals"])
    # present_results(games)

    # caller.close()

    notification = create_notification()
    print(notification)

if __name__ == "__main__":
    main()
