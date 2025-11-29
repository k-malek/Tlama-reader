"""Database module for storing and retrieving board game data."""

import sqlite3
import json
from typing import Optional
from model.board_game import BoardGame


DB_FILE = "games.db"


def _get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Initialize the database with required tables."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            url TEXT PRIMARY KEY,
            name TEXT,
            final_price TEXT,
            distributor TEXT,
            category TEXT,
            weight_kg REAL,
            ean TEXT,
            game_type TEXT,
            min_age INTEGER,
            game_language TEXT,
            rules_language TEXT,
            min_players INTEGER,
            max_players INTEGER,
            play_time_minutes INTEGER,
            bgg_rating REAL,
            complexity REAL,
            author TEXT,
            game_categories TEXT,
            game_mechanics TEXT,
            year_published INTEGER,
            artists TEXT,
            my_rating REAL,
            has_demonic_vibe INTEGER DEFAULT 0,
            owned INTEGER DEFAULT 0,
            image TEXT
        )
    """)
    # Add owned column if it doesn't exist (for existing databases)
    try:
        cursor.execute("""
            ALTER TABLE games ADD COLUMN owned INTEGER DEFAULT 0
        """)
    except sqlite3.OperationalError:
        pass  # Column already exists
    conn.commit()
    conn.close()


def game_exists(url: str) -> bool:
    """Check if a game with the given URL exists in the database."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM games WHERE url = ?", (url,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def save_game(board_game: BoardGame):
    """Save a BoardGame instance to the database."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()

    def encode_list(value):
        if value is None:
            return None
        if isinstance(value, list):
            return json.dumps(value)
        return value

    def ensure_not_list(value):
        if isinstance(value, list):
            return json.dumps(value) if value else None
        return value

    cursor.execute("""
        INSERT OR REPLACE INTO games (
            url, name, final_price, distributor, category,
            weight_kg, ean, game_type, min_age, game_language, rules_language,
            min_players, max_players, play_time_minutes, bgg_rating, complexity,
            author, game_categories, game_mechanics, year_published, artists, my_rating,
            has_demonic_vibe, owned, image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        board_game.url,
        ensure_not_list(board_game.name),
        ensure_not_list(board_game.final_price),
        ensure_not_list(board_game.distributor),
        ensure_not_list(board_game.category),
        board_game.weight_kg,
        ensure_not_list(board_game.ean),
        ensure_not_list(board_game.game_type),
        board_game.min_age,
        ensure_not_list(board_game.game_language),
        encode_list(board_game.rules_language),
        board_game.min_players,
        board_game.max_players,
        board_game.play_time_minutes,
        board_game.bgg_rating,
        board_game.complexity,
        ensure_not_list(board_game.author),
        encode_list(board_game.game_categories),
        encode_list(board_game.game_mechanics),
        board_game.year_published,
        encode_list(board_game.artists),
        board_game.my_rating,
        1 if getattr(board_game, 'has_demonic_vibe', 0) else 0,
        1 if getattr(board_game, 'owned', 0) else 0,
        getattr(board_game, 'image', None)
    ))
    conn.commit()
    conn.close()


def load_game(url: str) -> Optional[BoardGame]:
    """Load a BoardGame instance from the database and recalculate rating."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games WHERE url = ?", (url,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    board_game = BoardGame.__new__(BoardGame)
    board_game.url = row['url']
    board_game.html_page_data = None
    board_game.parameters = {}
    board_game.my_rating = 0

    board_game.name = row['name']
    board_game.final_price = row['final_price']
    board_game.distributor = row['distributor']
    board_game.category = row['category']
    board_game.weight_kg = row['weight_kg']
    board_game.ean = row['ean']
    board_game.game_type = row['game_type']
    board_game.min_age = row['min_age']
    board_game.game_language = row['game_language']
    board_game.rules_language = json.loads(row['rules_language']) if row['rules_language'] else None
    board_game.min_players = row['min_players']
    board_game.max_players = row['max_players']
    board_game.play_time_minutes = row['play_time_minutes']
    board_game.bgg_rating = row['bgg_rating']
    board_game.complexity = row['complexity']
    board_game.author = row['author']
    board_game.game_categories = json.loads(row['game_categories']) if row['game_categories'] else None
    board_game.game_mechanics = json.loads(row['game_mechanics']) if row['game_mechanics'] else None
    board_game.year_published = row['year_published']
    board_game.artists = json.loads(row['artists']) if row['artists'] else None
    try:
        board_game.has_demonic_vibe = bool(row['has_demonic_vibe'])
    except (KeyError, IndexError):
        board_game.has_demonic_vibe = 0
    try:
        board_game.owned = bool(row['owned'])
    except (KeyError, IndexError):
        board_game.owned = False
    try:
        board_game.image = row['image']
    except (KeyError, IndexError):
        board_game.image = None

    old_rating = row['my_rating']
    board_game.rate()
    new_rating = board_game.my_rating

    if old_rating != new_rating:
        cursor.execute("UPDATE games SET my_rating = ? WHERE url = ?", (new_rating, url))
        conn.commit()

    conn.close()
    return board_game


def get_all_games(limit: Optional[int] = None, order_by: str = "my_rating DESC") -> list:
    """Get all games from database, optionally limited and ordered."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()

    # Safe order_by values
    allowed_order_by = ["my_rating DESC", "my_rating ASC", "name ASC", "name DESC", "final_price ASC", "final_price DESC"]
    if order_by not in allowed_order_by:
        order_by = "my_rating DESC"

    query = f"SELECT * FROM games ORDER BY {order_by}"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    games = []
    for row in rows:
        game = _row_to_board_game(row)
        if game:
            games.append(game)
    return games


def search_games_in_db(name: Optional[str] = None, min_rating: Optional[float] = None,
                       max_price: Optional[int] = None, distributor: Optional[str] = None,
                       limit: Optional[int] = None) -> list:
    """Search games in database with filters."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if name:
        conditions.append("name LIKE ?")
        params.append(f"%{name}%")

    if min_rating is not None:
        conditions.append("my_rating >= ?")
        params.append(min_rating)

    if max_price is not None:
        conditions.append("CAST(final_price AS INTEGER) <= ?")
        params.append(max_price)

    if distributor:
        conditions.append("distributor LIKE ?")
        params.append(f"%{distributor}%")

    query = "SELECT * FROM games"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY my_rating DESC"

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    games = []
    for row in rows:
        game = _row_to_board_game(row)
        if game:
            games.append(game)
    return games


def _row_to_board_game(row) -> Optional[BoardGame]:
    """Convert a database row to a BoardGame instance."""
    try:
        board_game = BoardGame.__new__(BoardGame)
        board_game.url = row['url']
        board_game.html_page_data = None
        board_game.parameters = {}
        board_game.my_rating = 0

        board_game.name = row['name']
        board_game.final_price = row['final_price']
        board_game.distributor = row['distributor']
        board_game.category = row['category']
        board_game.weight_kg = row['weight_kg']
        board_game.ean = row['ean']
        board_game.game_type = row['game_type']
        board_game.min_age = row['min_age']
        board_game.game_language = row['game_language']
        board_game.rules_language = json.loads(row['rules_language']) if row['rules_language'] else None
        board_game.min_players = row['min_players']
        board_game.max_players = row['max_players']
        board_game.play_time_minutes = row['play_time_minutes']
        board_game.bgg_rating = row['bgg_rating']
        board_game.complexity = row['complexity']
        board_game.author = row['author']
        board_game.game_categories = json.loads(row['game_categories']) if row['game_categories'] else None
        board_game.game_mechanics = json.loads(row['game_mechanics']) if row['game_mechanics'] else None
        board_game.year_published = row['year_published']
        board_game.artists = json.loads(row['artists']) if row['artists'] else None
        # sqlite3.Row doesn't support .get(), use try/except or check keys
        try:
            board_game.has_demonic_vibe = bool(row['has_demonic_vibe'])
        except (KeyError, IndexError):
            board_game.has_demonic_vibe = False
        try:
            board_game.owned = bool(row['owned'])
        except (KeyError, IndexError):
            board_game.owned = False
        try:
            board_game.image = row['image']
        except (KeyError, IndexError):
            board_game.image = None

        board_game.rate()
        return board_game
    except Exception as e:
        print(f"Error converting row to BoardGame: {e}")
        return None


def update_game_boolean(url: str, field: str, value: bool) -> bool:
    """Update a boolean field (owned or has_demonic_vibe) for a game."""
    # SQLite doesn't support parameterized column names, so we use explicit if-elif
    # to avoid string interpolation and prevent SQL injection
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()

    if field == 'owned':
        cursor.execute("UPDATE games SET owned = ? WHERE url = ?", (1 if value else 0, url))
    elif field == 'has_demonic_vibe':
        cursor.execute("UPDATE games SET has_demonic_vibe = ? WHERE url = ?", (1 if value else 0, url))
    else:
        conn.close()
        return False

    conn.commit()
    conn.close()
    return True


def get_game_count() -> int:
    """Get total number of games in database."""
    _init_db()
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM games")
    count = cursor.fetchone()[0]
    conn.close()
    return count

