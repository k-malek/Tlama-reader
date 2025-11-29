# Tlama Reader

An automated tool for monitoring and analyzing board games from [Tlama Games](https://www.tlamagames.com), a Czech board game retailer. The tool checks for daily promo games, searches and rates games based on customizable preferences, and sends notifications when high-rated games are found.

## Features

### 🎯 Promo Game Monitoring
- **Daily Promo Check**: Automatically fetches the current promo game from Tlama Games homepage
- **Weekly Best Deals**: Finds the best discounted deals every week
- Rates games based on your preferences (price, categories, mechanics, BGG rating, etc.)
- Stores game data in a local SQLite database
- Sends OneSignal notifications when games exceed your rating threshold (default: 140)
- Weekly deals are highlighted with special styling in email notifications

### 🔍 Game Search & Filtering
- Search games with customizable filters (price range, categories, mechanics, difficulty, etc.)
- Filter by availability, game type, player count, play time, and more
- Rate and sort results by your personal preferences
- Supports category and mechanic filtering (e.g., `cat:card_game`, `mech:solo`)

### 📊 Intelligent Rating System
Games are automatically rated based on:
- **Price**: Lower prices get higher ratings
- **Distributor**: Preferences for specific publishers (e.g., Mindok bonus, Asmodee penalty)
- **Game Type**: Base games preferred over expansions
- **Player Count**: Solo games get bonus points
- **BGG Rating**: Higher BoardGameGeek ratings increase score
- **Play Time**: Optimal range preferred (30-120 minutes)
- **Categories**: Customizable favorite categories (e.g., dice games, card games)
- **Mechanics**: Preferred mechanics boost rating (e.g., solo, cooperative, dice rolling)

### 💾 Database Storage
- SQLite database (`games.db`) stores all game information
- Caches game data to avoid redundant web requests
- Automatically updates ratings when preferences change

### 🔔 OneSignal Integration
- Sends custom events to OneSignal when high-rated promo games are found
- Configurable rating threshold for notifications
- Includes full game data (name, price, rating, image, URL) in notifications

## Installation

### Using uv (Recommended)

**Sync the project** (creates virtual environment and installs dependencies):

```bash
uv sync
```

This will create a virtual environment at `.venv` and install all dependencies automatically.

**Run the script:**

```bash
# Run promo check (daily deals)
uv run python main.py promo

# Run best deals check (weekly deals)
uv run python main.py best-deals

# Search games
uv run python main.py search

# Check specific game
uv run python main.py game <url>
```

**Or activate the virtual environment:**

```bash
source .venv/bin/activate  # On macOS/Linux
python main.py promo
```

### Using pip

```bash
pip install -e .
```

Or install dependencies only:

```bash
pip install .
```

## Usage

### Basic Usage - Check Promo Game

**Using command line:**
```bash
uv run python main.py promo
```

**Using Python:**
```python
from website_caller import WebsiteCaller
from utils.promo import get_promo_game

caller = WebsiteCaller(timeout=30, use_browser=True)
promo_game = get_promo_game(caller)
print(promo_game.get_data_row())  # Name | Price | Rating | URL

caller.close()

# Send notification if rating is high enough
if promo_game.my_rating > 140:
    from integrations.onesignal_caller import send_custom_event
    send_custom_event(promo_game.to_json())
```

### Check Best Deals (Weekly)

**Using command line:**
```bash
uv run python main.py best-deals
```

**Using Python:**
```python
from website_caller import WebsiteCaller
from utils.search import search_for_game
from integrations.onesignal_caller import send_custom_event

caller = WebsiteCaller(timeout=30, use_browser=True)
games = search_for_game(caller, filters=["discounted"])
best_deal_game = games[0]
best_deal_game.deal = "weekly"  # Mark as weekly deal
send_custom_event(best_deal_game.to_json())
caller.close()
```

### Search Games with Filters

**Using command line:**
```bash
# Search without filters
uv run python main.py search

# Search with filters (pass filters as additional arguments)
uv run python main.py search amazing cheap cat:card_game mech:solo
```

**Using Python:**
```python
from website_caller import WebsiteCaller
from utils.search import search_for_game, present_results

caller = WebsiteCaller(timeout=30, use_browser=True)

# Search for games matching your criteria
games = search_for_game(
    caller,
    filters=["amazing", "cheap", "cat:card_game", "mech:solo"],
    pages=5  # Number of pages to search
)

# Display results sorted by rating
present_results(games)

caller.close()
```

### Available Filters

See `config.py` for all available filters. Examples:
- `"available"` - Only in-stock games
- `"discounted"` - Games on sale
- `"cheap"` - Price range 1-1200 Kč
- `"amazing"` - Highly rated games
- `"cat:card_game"` - Card game category
- `"mech:solo"` - Solo/cooperative mechanics

### Customize Preferences

Edit `config.py` to customize your game preferences:

```python
FAVORITES = {
    "categories": {
        "very_valuable": ["Kostkové"],  # Dice games
        "valuable": ["Karetní", "Dobrodružné", ...],
        "unwanted": ["Horror"]
    },
    "mechanics": {
        "very_valuable": ["Solo / Solitaire Game", "Cooperative Game", ...],
        "valuable": ["Hand Management", "Tile Placement", ...],
        "unwanted": ["Real-Time"]
    }
}
```

## Components

### WebsiteCaller
A utility component for making HTTP requests and browser automation. Used internally by the Tlama Reader for fetching game data.

**Features:**
- Standard HTTP requests (GET, POST, etc.)
- Browser automation with Playwright for JavaScript-heavy pages
- Session management and connection pooling
- Automatic URL validation

**Example:**
```python
from website_caller import WebsiteCaller

caller = WebsiteCaller(timeout=30, use_browser=True)

# Simple GET request
response = caller.get("https://example.com")

# Get HTML after JavaScript execution
html = caller.get_html_with_browser(
    url="https://example.com",
    wait_for_selector="#content",
    wait_until="networkidle"
)

caller.close()
```

## GitHub Actions Setup

This project includes two GitHub Actions workflows that automatically check for board game deals and send notifications via OneSignal.

### Setup Instructions

1. **Push your code to GitHub** (make sure the repository is public for free GitHub Actions)

2. **Add GitHub Secrets**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add the following secrets (see OneSignal Setup section for how to get these):
     - `ONESIGNAL_API_KEY` - Your OneSignal REST API key
     - `ONESIGNAL_ORGANIZATION_API_KEY` - Your OneSignal Organization API key (optional, for some endpoints)
     - `ONESIGNAL_APP_ID` - Your OneSignal App ID
     - `MY_USER_EXTERNAL_ID` - Your user's External ID (for custom events)
     - `MY_USER_ONESIGNAL_ID` - Your user's OneSignal ID (for custom events)

3. **The workflows will automatically run**:
   - **Daily Promo Check**: Runs daily at 6:30 AM UTC+1 (5:30 AM UTC) - checks for daily promo games
   - **Weekly Best Deals Check**: Runs every Monday at 7:30 AM UTC+1 (6:30 AM UTC) - checks for weekly best deals
   - You can also manually trigger either workflow from the Actions tab → Select workflow → "Run workflow"

### Workflow Details

#### Daily Promo Game Check (`.github/workflows/daily-run.yml`)
- Runs `python main.py promo` to check for daily promo games
- If a game has a rating > 140, it sends a custom event to OneSignal
- Scheduled to run daily at 6:30 AM UTC+1

#### Weekly Best Deals Check (`.github/workflows/weekly-run.yml`)
- Runs `python main.py best-deals` to find the best discounted deals
- Sets the `deal` parameter to "weekly" for special weekly deal styling in notifications
- Scheduled to run every Monday at 7:30 AM UTC+1 (1 hour after daily check)

Both workflows:
- Install Python 3.11+ and dependencies using `uv`
- Install Playwright browsers (Chromium)
- Use the same OneSignal secrets for notifications

### Viewing Workflow Runs

- Go to the "Actions" tab in your GitHub repository
- Click on "Daily Promo Game Check" or "Weekly Best Deals Check" to see run history
- Click on any run to see logs and debug issues

## Configuration

### OneSignal Setup

OneSignal is used to send push notifications and emails when high-rated promo games are found. Follow these steps to set up OneSignal:

#### 1. Create OneSignal Account and App

1. **Sign up for OneSignal** (free tier is sufficient): https://onesignal.com/
2. **Create a new app** in your OneSignal dashboard
   - Go to Dashboard → New App/Website
   - Choose a platform (Web Push, Email, or both)
   - Complete the setup wizard

#### 2. Get API Keys and App ID

1. **REST API Key**:
   - Go to Settings → Keys & IDs
   - Copy the **REST API Key** (this is your `ONESIGNAL_API_KEY`)

2. **Organization API Key** (optional but recommended):
   - Go to Settings → Account
   - Copy the **Organization API Key** (this is your `ONESIGNAL_ORGANIZATION_API_KEY`)

3. **App ID**:
   - Go to Settings → Keys & IDs
   - Copy the **App ID** (this is your `ONESIGNAL_APP_ID`)

#### 3. Create Push/Email Template

1. **Go to Messages → Templates** in your OneSignal dashboard
2. **Create a new template**:
   - Click "New Template"
   - Choose Email or Push Notification (or both)
   - Copy the content from `templates/deal_template.html` in this repository
   - The template uses Liquid syntax to display game data:
     - `{{ game.name }}` - Game name
     - `{{ game.final_price }}` - Price in Kč
     - `{{ game.my_rating }}` - Your custom rating
     - `{{ game.deal }}` - Deal type ("daily" or "weekly") - weekly deals get special styling
     - `{{ game.url }}` - Link to game page
     - And more game details (categories, mechanics, BGG rating, etc.)
   - The template automatically applies special styling for weekly deals (orange theme, prominent badges)
3. **Save the template** and note the Template ID (you may need it later)

#### 4. Create Custom Event Journey

1. **Go to Journeys** in your OneSignal dashboard
2. **Create a new Journey**:
   - Click "New Journey"
   - Choose "Custom Event" as the trigger
   - Set the event name to: `game_data` (this must match exactly)
   - Add your template as an action (Email or Push Notification)
   - Configure any additional conditions or delays
   - Save and activate the journey

#### 5. Get User Identification (for Custom Events)

The custom event needs to identify which user to send the notification to:

1. **Go to Audience → All Users** in your OneSignal dashboard
2. **Select a user** (or create a test user)
3. **Copy the following values**:
   - **External ID** (this is your `MY_USER_EXTERNAL_ID`)
   - **OneSignal ID** (this is your `MY_USER_ONESIGNAL_ID`)

   Note: If you don't have a user yet, you can create one by:
   - Adding a subscriber to your app (via web push subscription or email subscription)
   - Or using the OneSignal API to create a user

#### 6. Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# OneSignal Configuration
ONESIGNAL_API_KEY=your_rest_api_key_here
ONESIGNAL_ORGANIZATION_API_KEY=your_organization_api_key_here
ONESIGNAL_APP_ID=your_app_id_here

# User Identification (required for custom events)
MY_USER_EXTERNAL_ID=your_external_id_here
MY_USER_ONESIGNAL_ID=your_onesignal_id_here
```

**Important**:
- Replace all placeholder values with your actual OneSignal credentials
- Never commit the `.env` file to version control (it's already in `.gitignore`)
- For GitHub Actions, add these as secrets (see GitHub Actions Setup section)

### Rating Threshold

Edit `main.py` to change the notification threshold:

```python
if promo_game.my_rating > 140:  # Change this value
    send_custom_event(promo_game.to_json())
```

### Testing OneSignal Integration

To test if everything is set up correctly:

```python
from integrations.onesignal_caller import send_custom_event

# Test with sample game data
test_game = {
    "name": "Test Game",
    "final_price": "999",
    "my_rating": 200,
    "url": "https://www.tlamagames.com/test",
    # ... other game fields
}

send_custom_event(test_game)
```

Check your OneSignal dashboard → Events to see if the custom event was received, and verify that your journey triggered correctly.

## Project Structure

```
.
├── main.py                 # Main entry point (supports: promo, best-deals, search, game)
├── website_caller.py       # HTTP/browser utility component
├── config.py              # Configuration (filters, preferences)
├── database.py            # SQLite database operations
├── model/
│   └── board_game.py      # BoardGame data model and rating logic
├── utils/
│   ├── promo.py           # Promo game fetching
│   └── search.py          # Game search functionality
├── integrations/
│   └── onesignal_caller.py # OneSignal notification integration
├── templates/
│   └── deal_template.html # Email template for deal notifications (supports daily/weekly styling)
├── .github/
│   └── workflows/
│       ├── daily-run.yml  # Daily promo check workflow
│       └── weekly-run.yml # Weekly best deals check workflow
└── games.db               # SQLite database (created automatically)
```

## Requirements

- Python 3.11+
- Playwright (for browser automation)
- BeautifulSoup4 (for HTML parsing)
- requests (for HTTP requests)
- onesignal-sdk-python (for notifications)

All dependencies are specified in `pyproject.toml` and will be installed automatically with `uv sync`.

## License

This project is for personal use to monitor Tlama Games promotions.
