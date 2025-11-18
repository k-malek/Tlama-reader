from bs4 import BeautifulSoup
from config import FAVORITES


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

    def __init__(self, html_page_data, url):
        self.html_page_data = html_page_data
        self.url = url
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
        self.parameters = {}
        self.from_html(html_page_data)
        self.rate()

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
                    return 300  # Fixed value for "X+" format
                # Handle "do 15" (up to 15) -> convert to 10
                if value_str.lower().startswith('do '):
                    try:
                        max_time = int(value_str.split()[1])
                        return 10  # Fixed value for "up to X" format
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

    def from_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        self.name = soup.find('h1').text.strip() if soup.find('h1') else None
        self.final_price = soup.find('span', class_='price-final-holder').text.replace(' ', '').replace('Kč', '').strip() if soup.find('span', class_='price-final-holder') else None
        
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
            
            # Parse comma-separated values
            if "," in value:
                value = [v.strip() for v in value.split(",")]
            else:
                value = value
            
            self.parameters[key] = value
            
            # Map to attributes
            attr_name = self.PARAMETER_MAPPING.get(key)
            if attr_name:
                parsed_value = self._parse_value(key, value)
                setattr(self, attr_name, parsed_value)


    def get_data_row(self):
        return f"{self.name} | {self.final_price} Kč | {self.my_rating} | {self.url}"

    def print_all_info(self):
        print(self.name, self.final_price+" Kč", self.distributor, self.category, self.weight_kg, self.ean, self.game_type, self.min_age, self.game_language, self.rules_language, self.min_players, self.max_players, self.play_time_minutes, self.bgg_rating, self.complexity, self.author, self.game_categories, self.game_mechanics, self.year_published, self.artists)

    def rate(self):
        self.my_rating = 0

        # Vibe

        if self.has_demonic_vibe:
            self.my_rating -= 10000
            return self.my_rating

        # Price
        if self.final_price is not None:
            final_price = int(self.final_price)
            if final_price < 500:
                self.my_rating += 50
            elif final_price < 1000:
                self.my_rating += 20
            elif final_price < 1200:
                self.my_rating += 5
            elif final_price >= 1200 and final_price < 2000:
                pass
            else:
                self.my_rating -= 50

        # Distributor
        if self.distributor == 'Mindok':
            self.my_rating += 10
        elif self.distributor == 'Asmodee Czech Republic':
            self.my_rating -= 10000
            return self.my_rating

        # Základní hra / rozšíření
        if self.game_type == 'Základní hra':
            self.my_rating += 10
        elif self.game_type == 'Rozšíření':
            self.my_rating -= 10
            return self.my_rating

        # Min players
        if self.min_players == 1:
            self.my_rating += 10

        # BGG rating
        if self.bgg_rating is not None:
            if self.bgg_rating >= 8:
                self.my_rating += 20
            elif self.bgg_rating >= 7.5:
                self.my_rating += 10
            elif self.bgg_rating >= 7:
                self.my_rating += 5
            elif self.bgg_rating <= 6:
                self.my_rating -= 20
            elif self.bgg_rating <= 5:
                self.my_rating -= 40

        # Play time
        if self.play_time_minutes is not None:
            if self.play_time_minutes > 120:
                self.my_rating -= 10
            elif self.play_time_minutes <= 30:
                self.my_rating -= 50

        # Game categories
        if self.game_categories is not None:
            very_valueable_categories = FAVORITES['categories']['very_valuable']
            valueable_categories = FAVORITES['categories']['valuable']
            unwanted_categories = FAVORITES['categories']['unwanted']

            for category in self.game_categories:
                if category in very_valueable_categories:
                    self.my_rating += 50
                if category in valueable_categories:
                    self.my_rating += 15
                if category in unwanted_categories:
                    self.my_rating -= 100
                    return self.my_rating

        # Game mechanics
        if self.game_mechanics is not None:
            very_valueable_mechanics = FAVORITES['mechanics']['very_valuable']
            valueable_mechanics = FAVORITES['mechanics']['valuable']
            unwanted_mechanics = FAVORITES['mechanics']['unwanted']

            for mechanic in self.game_mechanics:
                if mechanic in very_valueable_mechanics:
                    self.my_rating += 50
                if mechanic in valueable_mechanics:
                    self.my_rating += 10
                if mechanic in unwanted_mechanics:
                    self.my_rating -= 100
                    return self.my_rating

        return self.my_rating

    def to_json(self):
        """Convert BoardGame instance to a JSON-serializable dictionary."""
        return {
            'url': self.url,
            'name': self.name,
            'final_price': self.final_price,
            'distributor': self.distributor,
            'game_type': self.game_type,
            'min_age': self.min_age,
            'game_language': self.game_language,
            'rules_language': self.rules_language,
            'min_players': self.min_players,
            'max_players': self.max_players,
            'play_time_minutes': self.play_time_minutes,
            'bgg_rating': self.bgg_rating,
            'complexity': self.complexity,
            'game_categories': self.game_categories,
            'game_mechanics': self.game_mechanics,
            'year_published': self.year_published,
            'parameters': self.parameters,
            'my_rating': self.my_rating,
            'image': self.image
        }
