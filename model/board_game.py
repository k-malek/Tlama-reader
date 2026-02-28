from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from config import (
    BGG_TIERS,
    FAVORITES,
    RATING_CATEGORY_CAP,
    RATING_COMPLEXITY_BONUS,
    RATING_DISCOUNT_MAX,
    RATING_DISCOUNT_PER_10_PCT,
    RATING_MECHANIC_CAP,
    RATING_PLAY_TIME_FILLER_PENALTY,
)


def _get_row_bool(row: Any, key: str) -> bool:
    """Safely get a boolean from a DB row (handles missing columns)."""
    try:
        return bool(row[key])
    except (KeyError, IndexError):
        return False


def _get_row_value(row: Any, key: str) -> Any:
    """Safely get a value from a DB row (handles missing columns)."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


# Magic numbers used in rating algorithm
RATING_PENALTY_DEMONIC = 10000
RATING_PENALTY_ASMODEE = 10000
RATING_PENALTY_UNWANTED = 100
PLAY_TIME_FALLBACK_PLUS = 300  # For "181+" format
PLAY_TIME_FALLBACK_UP_TO = 10  # For "do 15" format


class BoardGame:
    # Mapping from Czech parameter names to English attribute names
    PARAMETER_MAPPING = {
        'Kategorie': 'category',
        'Hmotnost': 'weight_kg',
        'EAN': 'ean',
        '1. Základní hra / rozšíření': 'game_type',
        '2. Minimální věk': 'min_age',
        '3. Jazyk hry': 'game_language',
        '4. Jazyk pravidel': 'rules_language',
        '5. Minimální počet hráčů': 'min_players',
        '6. Maximální počet hráčů': 'max_players',
        '7. Herní doba (minut)': 'play_time_minutes',
        '8. Hodnocení Boardgamegeek (0-10)': 'bgg_rating',
        '9. Náročnost (1-5)': 'complexity',
        'Autor': 'author',
        'Herní kategorie': 'game_categories',
        'Herní mechaniky': 'game_mechanics',
        'Rok vydání': 'year_published',
        'Výtvarníci': 'artists',
    }
    
    # Fields that should be converted to integers
    INTEGER_FIELDS = {'min_age', 'min_players', 'max_players', 'play_time_minutes', 'year_published'}
    
    # Fields that should be converted to floats
    FLOAT_FIELDS = {'weight_kg', 'bgg_rating', 'complexity'}
    
    # Fields that are always lists
    LIST_FIELDS = {'rules_language', 'game_categories', 'game_mechanics', 'artists'}

    def __init__(self, html_page_data=None, url=None, deal='daily', skip_html_parsing=False):
        self.html_page_data = html_page_data
        self.url = url
        self.deal = deal
        self.name = None
        self.final_price = None
        self.distributor = None
        self.category = None
        self.weight_kg = None
        self.ean = None
        self.game_type = None
        self.min_age = None
        self.game_language = None
        self.rules_language = None
        self.min_players = None
        self.max_players = None
        self.play_time_minutes = None
        self.bgg_rating = None
        self.complexity = None
        self.author = None
        self.game_categories = None
        self.game_mechanics = None
        self.year_published = None
        self.artists = None
        self.has_demonic_vibe = 0
        self.image = None
        self.discount_percent: int | None = None
        self.original_price: str | None = None
        self.parameters = {}
        if not skip_html_parsing and html_page_data:
            self.from_html(html_page_data)
            self.rate()

    @classmethod
    def from_db_row(cls, row: Any) -> BoardGame:
        """Create a BoardGame from a database row (sqlite3.Row or dict-like)."""
        board_game = cls(html_page_data=None, url=row["url"], skip_html_parsing=True)
        board_game.parameters = {}
        board_game.my_rating = 0

        board_game.name = row["name"]
        board_game.final_price = row["final_price"]
        board_game.discount_percent = _get_row_value(row, "discount_percent")
        board_game.original_price = _get_row_value(row, "original_price")
        board_game.distributor = row["distributor"]
        board_game.category = row["category"]
        board_game.weight_kg = row["weight_kg"]
        board_game.ean = row["ean"]
        board_game.game_type = row["game_type"]
        board_game.min_age = row["min_age"]
        board_game.game_language = row["game_language"]
        board_game.rules_language = (
            json.loads(row["rules_language"]) if row["rules_language"] else None
        )
        board_game.min_players = row["min_players"]
        board_game.max_players = row["max_players"]
        board_game.play_time_minutes = row["play_time_minutes"]
        board_game.bgg_rating = row["bgg_rating"]
        board_game.complexity = row["complexity"]
        board_game.author = row["author"]
        board_game.game_categories = (
            json.loads(row["game_categories"]) if row["game_categories"] else None
        )
        board_game.game_mechanics = (
            json.loads(row["game_mechanics"]) if row["game_mechanics"] else None
        )
        board_game.year_published = row["year_published"]
        board_game.artists = (
            json.loads(row["artists"]) if row["artists"] else None
        )
        board_game.has_demonic_vibe = _get_row_bool(row, "has_demonic_vibe")
        board_game.owned = _get_row_bool(row, "owned")
        board_game.image = _get_row_value(row, "image")

        board_game.rate()
        return board_game

    def _parse_value(self, key, value):
        """Parse and convert value based on field type."""
        attr_name = self.PARAMETER_MAPPING.get(key)
        if not attr_name:
            return value
        
        # Handle list fields
        if attr_name in self.LIST_FIELDS:
            if isinstance(value, list):
                return value
            value_str = str(value)
            if "," in value_str:
                return [v.strip() for v in value_str.split(",")]
            return [value_str.strip()] if value_str.strip() else []
        
        # Handle integer fields
        if attr_name in self.INTEGER_FIELDS:
            if isinstance(value, list):
                # Take first value if it's a list
                value = value[0] if value else None
            if value is None:
                return None

            # Special handling for play_time_minutes with ranges (e.g., "61-90") or "do 15"
            if attr_name == 'play_time_minutes':
                value_str = str(value).strip()
                # Handle "neuvedena" (not stated) -> return 0
                if value_str.lower() == 'neuvedena':
                    return 0
                # Handle "181+" (181 or more) -> convert to 300
                if value_str.endswith('+'):
                    return PLAY_TIME_FALLBACK_PLUS
                # Handle "do 15" (up to 15) -> convert to 10
                if value_str.lower().startswith('do '):
                    try:
                        int(value_str.split()[1])
                        return PLAY_TIME_FALLBACK_UP_TO
                    except (ValueError, TypeError, IndexError):
                        return None
                # Handle ranges (e.g., "61-90")
                if '-' in value_str:
                    try:
                        parts = value_str.split('-')
                        if len(parts) == 2:
                            min_time = int(parts[0].strip())
                            max_time = int(parts[1].strip())
                            return int((min_time + max_time) / 2)
                    except (ValueError, TypeError):
                        return None

            try:
                return int(str(value).strip())
            except (ValueError, TypeError):
                return None
        
        # Handle float fields
        if attr_name in self.FLOAT_FIELDS:
            if isinstance(value, list):
                # Take first value if it's a list
                value = value[0] if value else None
            if value is None:
                return None
            try:
                # Remove 'kg' suffix if present
                value_str = str(value).replace(' kg', '').strip()
                return float(value_str) if value_str else None
            except (ValueError, TypeError):
                return None
        
        # Default: return as string or list
        if isinstance(value, list):
            return value
        value_str = str(value).strip()
        if not value_str:
            return None
        if "," in value_str:
            return [v.strip() for v in value_str.split(",")]
        return value_str

    def _normalize_price(self, text: str) -> str | None:
        """Extract numeric price from '1 999 Kč' (Czech format)."""
        raw = text.replace(' ', '').replace('Kč', '').replace('\n', '').strip()
        return raw if raw and raw.isdigit() else None

    def _parse_discount_percent(self, text: str) -> int | None:
        """Extract discount from '–10 %' or '-10%'."""
        cleaned = text.replace('%', '').replace(' ', '').strip().lstrip('–\-')
        return int(cleaned) if cleaned.isdigit() else None

    def _parse_price_text(self, text: str) -> None:
        """Parse price from wrapper text like '1 999 Kč –10 % 1 799 Kč' (no child elements)."""
        clean = text.replace('\n', ' ')
        if ' %' in clean:
            before_pct, after_pct = clean.split(' %', 1)
            pct_part = before_pct.split()[-1].lstrip('–\-')
            if pct_part.isdigit():
                self.discount_percent = int(pct_part)
            self.final_price = self._normalize_price(after_pct.split('Kč')[0] + 'Kč')
        for sep in (' –', ' -'):
            if sep in clean:
                self.original_price = self._normalize_price(clean.split(sep)[0] + 'Kč')
                break

    def from_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        self.name = soup.find('h1').text.strip() if soup.find('h1') else None

        # Parse price from main product block (price-standard, price-save, price-final-holder)
        price_wrapper = soup.find(class_='p-final-price-wrapper')
        if price_wrapper:
            std = price_wrapper.find(class_='price-standard')
            save = price_wrapper.find(class_='price-save')
            final = price_wrapper.find(class_='price-final-holder')
            if std:
                self.original_price = self._normalize_price(std.get_text())
            if final:
                self.final_price = self._normalize_price(final.get_text())
            elif std:
                self.final_price = self.original_price
            if save:
                self.discount_percent = self._parse_discount_percent(save.get_text())
            # Fallback when wrapper has only raw text (e.g. in tests)
            if self.final_price is None and price_wrapper.get_text(strip=True):
                self._parse_price_text(price_wrapper.get_text())
        # Fallback to price-final-holder only
        if self.final_price is None:
            holder = soup.find('span', class_='price-final-holder')
            if holder:
                self.final_price = self._normalize_price(holder.get_text())

        # Extract distributor/brand name
        brand_link = soup.find('a', {'data-testid': 'productCardBrandName'})
        if brand_link:
            span = brand_link.find('span')
            self.distributor = span.text.strip() if span else None
        
        # Extract main image URL from highlighted thumbnail
        highlighted_link = soup.find('a', class_='highlighted')
        if highlighted_link and highlighted_link.get('href'):
            self.image = highlighted_link['href']

        self.parameters = {}
        details_table = soup.find('div', class_='extended-description').find('table', class_='detail-parameters')
        
        if not details_table:
            raise ValueError("Details table not found")
        
        for row in details_table.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            if not th or not td:
                continue
                
            key = th.text.strip().replace('? ', '').rstrip(':')
            value = td.text.strip()
            
            # Skip empty keys or values
            if not key or not value:
                continue
            
            # Store original value in parameters
            original_value = value

            # Special handling for play_time_minutes: extract last range if comma-separated
            if key == '7. Herní doba (minut)' and ',' in value and '-' in value:
                # Extract the last range from comma-separated values
                comma_parts = [p.strip() for p in value.split(',')]
                # Find the last part that contains a hyphen (the last range)
                for part in reversed(comma_parts):
                    if '-' in part:
                        value = part.strip()
                        break

            # Parse comma-separated values
            if "," in value:
                value = [v.strip() for v in value.split(",")]
            else:
                value = value
            
            self.parameters[key] = original_value
            
            # Map to attributes
            attr_name = self.PARAMETER_MAPPING.get(key)
            if attr_name:
                parsed_value = self._parse_value(key, value)
                setattr(self, attr_name, parsed_value)


    def get_data_row(self):
        return f"{self.name} | {self.final_price} Kč | {self.my_rating} | {self.url}"

    def print_all_info(self):
        """Print board game information in a nice table format."""
        # Define fields to display with their labels
        price_str = None
        if self.final_price:
            if self.original_price and self.discount_percent:
                price_str = f"{self.original_price} Kč (−{self.discount_percent}%) → {self.final_price} Kč"
            else:
                price_str = f"{self.final_price} Kč"
        fields = [
            ('Name', self.name),
            ('Price', price_str),
            ('Rating', self.my_rating),
            ('Distributor', self.distributor),
            ('Category', self.category),
            ('Game Type', self.game_type),
            ('Author', self.author),
            ('Year Published', self.year_published),
            ('Min Age', self.min_age),
            ('Players', f"{self.min_players}-{self.max_players}" if self.min_players and self.max_players else (self.min_players or self.max_players)),
            ('Play Time', f"{self.play_time_minutes} min" if self.play_time_minutes else None),
            ('BGG Rating', f"{self.bgg_rating:.1f}" if self.bgg_rating else None),
            ('Complexity', f"{self.complexity:.1f}" if self.complexity else None),
            ('Weight', f"{self.weight_kg} kg" if self.weight_kg else None),
            ('EAN', self.ean),
            ('Game Language', self.game_language),
            ('Rules Language', ', '.join(self.rules_language) if isinstance(self.rules_language, list) else self.rules_language),
            ('Categories', ', '.join(self.game_categories) if isinstance(self.game_categories, list) else self.game_categories),
            ('Mechanics', ', '.join(self.game_mechanics) if isinstance(self.game_mechanics, list) else self.game_mechanics),
            ('Artists', ', '.join(self.artists) if isinstance(self.artists, list) else self.artists),
        ]

        # Filter out None values and format as table
        max_label_width = max(len(label) for label, _ in fields)

        print("\n" + "=" * 60)
        for label, value in fields:
            if value is not None:
                print(f"{label:<{max_label_width}} : {value}")
        print("=" * 60 + "\n")

    def rate(self):
        self.my_rating = 0

        # Vibe
        if self.has_demonic_vibe:
            self.my_rating -= RATING_PENALTY_DEMONIC
            return self.my_rating

        # Distributor (Asmodee instant reject)
        if self.distributor == 'Asmodee Czech Republic':
            self.my_rating -= RATING_PENALTY_ASMODEE
            return self.my_rating

        # BGG as foundation (primary quality signal)
        if self.bgg_rating is not None:
            for threshold, points in BGG_TIERS:
                if self.bgg_rating >= threshold:
                    self.my_rating += points
                    break

        # Price (rebalanced): favor cheaper when otherwise similar; finer tiers so
        # e.g. 1499 Kč beats 1629 Kč, 1449 Kč beats 1499 Kč (same game, different language)
        # despite higher % off on the more expensive variant
        if self.final_price is not None:
            final_price = int(self.final_price)
            if final_price < 500:
                self.my_rating += 15
            elif final_price < 1000:
                self.my_rating += 10
            elif final_price < 1200:
                self.my_rating += 5
            elif final_price < 1450:
                self.my_rating += 18
            elif final_price < 1500:
                self.my_rating += 15
            elif final_price < 1800:
                self.my_rating += 2
            elif final_price < 2000:
                pass
            else:
                self.my_rating -= 30

        # Discount (reduced: +1 per 10%, max 10)
        if self.discount_percent is not None and self.discount_percent > 0:
            bonus = min(
                self.discount_percent * RATING_DISCOUNT_PER_10_PCT // 10,
                RATING_DISCOUNT_MAX,
            )
            self.my_rating += bonus

        # Mindok
        if self.distributor == 'Mindok':
            self.my_rating += 10

        # Solo
        if self.min_players == 1:
            self.my_rating += 10

        # Complexity bonus (depth signal for substantial games)
        if (
            self.complexity is not None
            and self.complexity >= 3.5
            and self.bgg_rating is not None
            and self.bgg_rating >= 7.5
        ):
            self.my_rating += RATING_COMPLEXITY_BONUS

        # Play time (only penalty for filler < 30 min)
        if self.play_time_minutes is not None and self.play_time_minutes <= 30:
            self.my_rating -= RATING_PLAY_TIME_FILLER_PENALTY

        # Game categories (capped)
        if self.game_categories is not None:
            very_valuable = FAVORITES['categories']['very_valuable']
            valuable = FAVORITES['categories']['valuable']
            unwanted = FAVORITES['categories']['unwanted']

            for category in self.game_categories:
                if category in unwanted:
                    self.my_rating -= RATING_PENALTY_UNWANTED
                    return self.my_rating

            cat_score = 0
            has_very = any(c in very_valuable for c in self.game_categories)
            valuable_count = sum(1 for c in self.game_categories if c in valuable)
            if has_very:
                cat_score += 30
            cat_score += valuable_count * 10
            self.my_rating += min(cat_score, RATING_CATEGORY_CAP)

        # Game mechanics (capped; very_valuable counts once to prevent stacking)
        if self.game_mechanics is not None:
            very_valuable = FAVORITES['mechanics']['very_valuable']
            valuable = FAVORITES['mechanics']['valuable']
            unwanted = FAVORITES['mechanics']['unwanted']

            for mechanic in self.game_mechanics:
                if mechanic in unwanted:
                    self.my_rating -= RATING_PENALTY_UNWANTED
                    return self.my_rating

            has_very = any(m in very_valuable for m in self.game_mechanics)
            valuable_count = sum(1 for m in self.game_mechanics if m in valuable)
            mech_score = (30 if has_very else 0) + valuable_count * 8
            self.my_rating += min(mech_score, RATING_MECHANIC_CAP)

        return self.my_rating

    def to_json(self):
        """Convert BoardGame instance to a JSON-serializable dictionary."""
        return {
            'url': self.url,
            'name': self.name,
            'final_price': self.final_price,
            'game_type': self.game_type,
            'min_age': self.min_age,
            'min_players': self.min_players,
            'max_players': self.max_players,
            'play_time_minutes': self.play_time_minutes,
            'bgg_rating': self.bgg_rating,
            'complexity': self.complexity,
            'game_categories': self.game_categories,
            'game_mechanics': self.game_mechanics,
            'my_rating': self.my_rating,
            'image': self.image,
            'deal': self.deal
        }
