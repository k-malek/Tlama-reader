"""Configuration constants for the Tlama caller application."""

BASE_URL = "https://www.tlamagames.com"

ENDPOINTS = {
    "shop": "/deskove-hry/",
    "promo": "/blue-friday/",
    "game": "/{game_url}",
}

FILTERS = {
    "available":"stock=1",
    "games_only":"pv117=2127",
    "discounted":"dd=1",
    "for_one_player":"pv129=2142",
    "simple":"pv141=2409,14496,14553,13704,14583,14499,14613,13761,14193,14052,2367,14067,14352,14079,13746,6316",
    "medium":"pv141=6316,14217,14082,13596,14382,2205,13935,4898,13998,13644",
    "complex":"pv141=4520,14394,15450,14325,14994,2271,15288,14334,16470,16482,18048,15717,4904,26046",
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
