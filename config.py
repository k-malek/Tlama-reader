"""Configuration constants for the Tlama caller application."""

import logging
import os

logger = logging.getLogger(__name__)

BASE_URL = "https://www.tlamagames.com"

# Deal tiers (from DB percentiles on positive-rated games, rounded up to 10)
# Used in deal_template.html for Nice / Great / Outstanding labels
RATING_NICE = 70      # top 50%
RATING_GREAT = 140    # top 25%
RATING_OUTSTANDING = 230  # top 10%

# Minimum rating threshold for sending OneSignal notifications
MIN_RATING_FOR_NOTIFICATION = RATING_NICE

# Daily promo: only notify for these game types (skip expansions, accessories, etc.)
PROMO_ACCEPTED_GAME_TYPES = ["Základní hra"]

# Rating algorithm: BGG tier points (primary quality signal)
BGG_TIERS = [
    (8.5, 235),
    (8.0, 219),
    (7.5, 130),
    (7.0, 40),
    (6.5, 25),
    (6.0, 5),
    (5.0, -25),
    (0.0, -55),
]
RATING_CATEGORY_CAP = 40
RATING_MECHANIC_CAP = 50
RATING_DISCOUNT_PER_10_PCT = 1
RATING_DISCOUNT_MAX = 10
RATING_COMPLEXITY_BONUS = 50  # when complexity >= 3.5 and bgg >= 7.5
RATING_PLAY_TIME_FILLER_PENALTY = 40  # games < 30 min

# OneSignal environment variable names
ONESIGNAL_ENV_VARS = [
    "ONESIGNAL_APP_ID",
    "ONESIGNAL_API_KEY",
    "MY_USER_EXTERNAL_ID",
    "MY_USER_ONESIGNAL_ID",
]


def validate_onesignal_env() -> bool:
    """Validate that OneSignal-related environment variables are set. Logs warnings for missing vars."""
    missing = [var for var in ONESIGNAL_ENV_VARS if not os.getenv(var)]
    if missing:
        logger.warning("OneSignal integration may fail: missing env vars: %s", ", ".join(missing))
        return False
    return True

ENDPOINTS = {
    "shop": "/deskove-hry/",
    "promo": "/jarni-vyprodej/",
    "game": "/{game_url}",
}

# Map English/other-language paths to Czech (CZK prices)
_URL_TO_CZK = [
    ("/en/board-games/", "/deskove-hry/"),
]


def to_czk_game_url(url: str) -> str:
    """Convert a game URL to the Czech version so prices are in CZK."""
    for en_path, cz_path in _URL_TO_CZK:
        if en_path in url:
            return url.replace(en_path, cz_path, 1)
    return url

FILTERS = {
    "available":"stock=1",
    "games_only":"pv117=2127",
    "discounted":"dd=1",
    "for_one_player":"pv129=2142",
    "simple":"pv141=2409,14496,14553,13704,14583,14499,14613,13761,14193,14052,2367,14067,14352,14079,13746,6316",
    "medium":"pv141=6316,14217,14082,13596,14382,2205,13935,4898,13998,13644,4520,14394",
    "complex":"pv141=14394,15450,14325,14994,2271,15288,14334,16470,16482,18048,15717,4904,26046",
    "good":"pv138=2316,14004,4895,13593,14112,14028,13701,6313,13635,6229,2172,13968,13641,14940,14166,14991,17616,15069,17001,4886,2484,23652,21855,23634,18087,19497,22836,26457,6307",
    "amazing":"pv138=2172,13968,13641,14940,14166,14991,17616,15069,17001,4886,2484,23652,21855,23634,18087,19497,22836,26457,6307",
    "very_cheap":"priceMin=1&priceMax=700",
    "cheap":"priceMin=1&priceMax=1200",
    "normal_price":"priceMin=1200&priceMax=2400",
    "expensive":"priceMin=2400&priceMax=3600",
    "very_expensive":"priceMin=3600",
    "no_language_required":"pv123=2133",
    "game_in_polish":"pv123=2553",
    "english_rulebook":"pv126=2139",
    # Categories, use "cat:card_game"
    "card_game":"13707",
    "adventure":"13860",
    "dice_game":"13797",
    "logic_game":"14055",
    "animals":"13971",
    # Mechanics, use "mech:dice_rolling"
    "solo":"13620",
    "cooperative":"13830",
    "dice_rolling":"13803",
    "modular_board":"13875"
}

# Metadata to identify which filters are categories and which are mechanics
# These lists contain the filter keys that should be prefixed with "cat:" or "mech:" in searches
CATEGORY_FILTERS = ["card_game", "adventure", "dice_game", "logic_game", "animals"]
MECHANIC_FILTERS = ["solo", "cooperative", "dice_rolling", "modular_board"]

# Filter groups for UI organization
FILTER_GROUPS = {
    "Price": ["discounted","very_cheap", "cheap", "normal_price", "expensive", "very_expensive"],
    "Difficulty": ["simple", "medium", "complex"],
    "Quality": ["good", "amazing"],
    "Players": ["for_one_player"],
    "Language": ["no_language_required", "game_in_polish", "english_rulebook"],
}

FAVORITES = {
    "categories": {
        "very_valuable": ["Kostkové"],
        "valuable": [
            "Karetní", "Dobrodružné", "Fantasy", "Průzkum vesmíru",
            "Sci-fi", "Ekonomické", "Průzkum", "Bludiště",
            "Kostkové", "Logické", "Zvířata"],
        "unwanted": ["V reálném čase", "Horror"]
    },
    "mechanics": {
        "very_valuable": [
            "Solo / Solitaire Game", "Cooperative Game","Modular Board", "Dice Rolling"],
        "valuable": [
            "Variable Set-up", "Scenario / Mission / Campaign Game",
            "Hand Management", "Tile Placement", "Open Drafting",
            "Variable Player Powers", "Tech Trees / Tech Tracks"],
        "unwanted": ["Real-Time"]
    }
}
