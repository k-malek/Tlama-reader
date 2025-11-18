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
            has_demonic_vibe INTEGER DEFAULT 0
        )
    """)
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
            has_demonic_vibe
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        1 if getattr(board_game, 'has_demonic_vibe', 0) else 0
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
    
    old_rating = row['my_rating']
    board_game.rate()
    new_rating = board_game.my_rating
    
    if old_rating != new_rating:
        cursor.execute("UPDATE games SET my_rating = ? WHERE url = ?", (new_rating, url))
        conn.commit()
    
    conn.close()
    return board_game

