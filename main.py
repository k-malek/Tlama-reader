from website_caller import WebsiteCaller
from utils.promo import get_promo_game


def main():
    caller = WebsiteCaller(timeout=30, use_browser=True)
    promo_game = get_promo_game(caller)
    print(promo_game.name, promo_game.final_price+" Kč", promo_game.my_rating)
    caller.close()

if __name__ == "__main__":
    main()
