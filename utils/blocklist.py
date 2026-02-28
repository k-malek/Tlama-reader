"""Blocklist of game URLs to exclude from notifications (evil/owned games)."""

import os
from pathlib import Path


def _normalize_url(url: str) -> str:
    """Normalize URL for consistent lookup (strip trailing slash, whitespace)."""
    return url.strip().rstrip("/")


def get_blocklist_path() -> Path:
    """Return the path to the blocklist file."""
    path = os.getenv("EXCLUDED_URLS_FILE")
    if not path:
        return Path(__file__).resolve().parent.parent / "excluded_game_urls.txt"
    return Path(path)


def load_excluded_urls() -> set[str]:
    """
    Load excluded game URLs from blocklist file.
    Returns empty set if file is missing.
    """
    path = get_blocklist_path()

    if not path.exists():
        return set()

    result: set[str] = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            result.add(_normalize_url(line))
    return result


def is_url_excluded(url: str, excluded: set[str] | None = None) -> bool:
    """Check if a game URL is in the excluded blocklist."""
    if excluded is None:
        excluded = load_excluded_urls()
    return _normalize_url(url) in excluded
