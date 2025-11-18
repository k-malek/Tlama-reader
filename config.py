"""Configuration constants for the Tlama caller application."""

BASE_URL = "https://www.tlamagames.com"

ENDPOINTS = {
    "shop": "/deskove-hry/",
    "game": "/{game_url}",
}

FILTERS = {
    "available":"stock=1",
    "games_only":"pv117=2127",
    "discounted":"dd=1",
    "for_one_player":"pv129=2142",
    "easy":"pv141=2409,14496,14553,13704,14583,14499,14613,13761,14193,14052,2367,14067,14352,14079,13746,6316",
    "hard":"pv141=6316,14217,14082,13596,14382,2205,13935,4898,13998,13644,4520,14394,15450,14325,14994,2271,15288,14334,16470,16482,18048,15717,4904,26046",
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
