from bs4 import BeautifulSoup


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
    INTEGER_FIELDS = {'min_age', 'min_players', 'max_players', 'play_time_minutes', 'year_published', 'complexity'}
    
    # Fields that should be converted to floats
    FLOAT_FIELDS = {'weight_kg', 'bgg_rating'}
    
    # Fields that are always lists
    LIST_FIELDS = {'rules_language', 'game_categories', 'game_mechanics', 'artists'}

    def __init__(self, html_page_data):
        self.html_page_data = html_page_data
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
        self.parameters = {}
        self.from_html(html_page_data)

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
