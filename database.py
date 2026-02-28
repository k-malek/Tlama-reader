"""Database module for storing and retrieving board game data."""

import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Optional

from model.board_game import BoardGame

logger = logging.getLogger(__name__)

DB_FILE: Path | str = Path("games.db")
_db_initialized = False


def set_db_path(path: str | Path) -> None:
    """Override database path (e.g. ':memory:' for tests). Resets init flag."""
    global DB_FILE, _db_initialized
    DB_FILE = path
    _db_initialized = False


def _get_connection():
    """Get database connection with context manager support."""
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    """Initialize the database with required tables (runs once)."""
    global _db_initialized
    if _db_initialized:
        return

    with closing(_get_connection()) as conn:
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
        for col_sql in [
            "ALTER TABLE games ADD COLUMN owned INTEGER DEFAULT 0",
            "ALTER TABLE games ADD COLUMN discount_percent INTEGER",
            "ALTER TABLE games ADD COLUMN original_price TEXT",
        ]:
            try:
                cursor.execute(col_sql)
            except sqlite3.OperationalError:
                pass  # Column already exists
        conn.commit()

    _db_initialized = True


def game_exists(url: str) -> bool:
    """Check if a game with the given URL exists in the database."""
    _init_db()
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM games WHERE url = ?", (url,))
        return cursor.fetchone() is not None


def _encode_list(value) -> Optional[str]:
    """Encode list as JSON for DB storage."""
    if value is None:
        return None
    if isinstance(value, list):
        return json.dumps(value)
    return value


def _ensure_not_list(value) -> Optional[str]:
    """Convert list to JSON string if needed."""
    if isinstance(value, list):
        return json.dumps(value) if value else None
    return value


def save_game(board_game: BoardGame) -> None:
    """Save a BoardGame instance to the database."""
    _init_db()
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO games (
                url, name, final_price, discount_percent, original_price, distributor, category,
                weight_kg, ean, game_type, min_age, game_language, rules_language,
                min_players, max_players, play_time_minutes, bgg_rating, complexity,
                author, game_categories, game_mechanics, year_published, artists, my_rating,
                has_demonic_vibe, owned, image
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            board_game.url,
            _ensure_not_list(board_game.name),
            _ensure_not_list(board_game.final_price),
            getattr(board_game, "discount_percent", None),
            getattr(board_game, "original_price", None),
            _ensure_not_list(board_game.distributor),
            _ensure_not_list(board_game.category),
            board_game.weight_kg,
            _ensure_not_list(board_game.ean),
            _ensure_not_list(board_game.game_type),
            board_game.min_age,
            _ensure_not_list(board_game.game_language),
            _encode_list(board_game.rules_language),
            board_game.min_players,
            board_game.max_players,
            board_game.play_time_minutes,
            board_game.bgg_rating,
            board_game.complexity,
            _ensure_not_list(board_game.author),
            _encode_list(board_game.game_categories),
            _encode_list(board_game.game_mechanics),
            board_game.year_published,
            _encode_list(board_game.artists),
            board_game.my_rating,
            1 if getattr(board_game, "has_demonic_vibe", 0) else 0,
            1 if getattr(board_game, "owned", 0) else 0,
            getattr(board_game, "image", None),
        ))
        conn.commit()


def load_game(url: str) -> Optional[BoardGame]:
    """Load a BoardGame instance from the database and recalculate rating."""
    _init_db()
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM games WHERE url = ?", (url,))
        row = cursor.fetchone()

    if not row:
        return None

    board_game = BoardGame.from_db_row(row)
    old_rating = row["my_rating"]
    new_rating = board_game.my_rating

    if old_rating != new_rating:
        with closing(_get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE games SET my_rating = ? WHERE url = ?", (new_rating, url))
            conn.commit()

    return board_game


_ORDER_QUERIES = {
    "my_rating DESC": "SELECT * FROM games ORDER BY my_rating DESC",
    "my_rating ASC": "SELECT * FROM games ORDER BY my_rating ASC",
    "name ASC": "SELECT * FROM games ORDER BY name ASC",
    "name DESC": "SELECT * FROM games ORDER BY name DESC",
    "final_price ASC": "SELECT * FROM games ORDER BY final_price ASC",
    "final_price DESC": "SELECT * FROM games ORDER BY final_price DESC",
}


def get_all_games(
    limit: Optional[int] = None, order_by: str = "my_rating DESC"
) -> list[BoardGame]:
    """Get all games from database, optionally limited and ordered."""
    _init_db()
    query = _ORDER_QUERIES.get(order_by, _ORDER_QUERIES["my_rating DESC"])

    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        if limit is not None:
            cursor.execute(query + " LIMIT ?", (limit,))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()

    games = []
    for row in rows:
        try:
            games.append(BoardGame.from_db_row(row))
        except Exception as e:
            logger.exception("Error converting row to BoardGame: %s", e)
    return games


def search_games_in_db(
    name: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price: Optional[int] = None,
    distributor: Optional[str] = None,
    limit: Optional[int] = None,
) -> list[BoardGame]:
    """Search games in database with filters."""
    _init_db()
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
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    games = []
    for row in rows:
        try:
            games.append(BoardGame.from_db_row(row))
        except Exception as e:
            logger.exception("Error converting row to BoardGame: %s", e)
    return games


def update_game_boolean(url: str, field: str, value: bool) -> bool:
    """Update a boolean field (owned or has_demonic_vibe) for a game."""
    _init_db()
    if field == "owned":
        sql = "UPDATE games SET owned = ? WHERE url = ?"
    elif field == "has_demonic_vibe":
        sql = "UPDATE games SET has_demonic_vibe = ? WHERE url = ?"
    else:
        return False

    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, (1 if value else 0, url))
        conn.commit()
    return True


def get_game_count() -> int:
    """Get total number of games in database."""
    _init_db()
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM games")
        return cursor.fetchone()[0]


def get_excluded_game_urls() -> list[str]:
    """Get URLs of games marked as owned or has_demonic_vibe (for export to blocklist)."""
    _init_db()
    with closing(_get_connection()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT url FROM games WHERE owned = 1 OR has_demonic_vibe = 1"
        )
        return [row["url"] for row in cursor.fetchall()]
