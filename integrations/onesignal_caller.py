import logging
import os
from datetime import date
from typing import Any, Optional

import onesignal

from config import (
    EMAIL_TEMPLATE_ID,
    GAME_TYPE_LABELS,
    WEEKLY_EMAIL_TEMPLATE_ID,
    RATING_GREAT,
    RATING_OUTSTANDING,
    validate_onesignal_env,
)
from onesignal.api import default_api
from onesignal.model.include_aliases import IncludeAliases
from onesignal.model.notification import Notification

logger = logging.getLogger(__name__)

# See configuration.py for a list of all supported configuration parameters.
# Some of the OneSignal endpoints require ORGANIZATION_API_KEY token for authorization, while others require REST_API_KEY.
# We recommend adding both of them in the configuration page so that you will not need to figure it out yourself.
configuration = onesignal.Configuration(
    rest_api_key = os.getenv("ONESIGNAL_API_KEY"), # App REST API key required for most endpoints
    organization_api_key = os.getenv("ONESIGNAL_ORGANIZATION_API_KEY") # Organization key is only required for creating new apps and other top-level endpoints
)

app_id = os.getenv("ONESIGNAL_APP_ID")


def _as_int(value: Any) -> int | None:
    """Coerce a price or count into an int, matching the email payload sample."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().replace(" ", "")
    if text.isdigit():
        return int(text)
    return None


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _map_game_type(value: Any) -> Any:
    """Map shop game_type values to email labels; a list is mapped item by item."""
    if isinstance(value, list):
        return [GAME_TYPE_LABELS.get(item, item) for item in value]
    if value is None:
        return None
    return GAME_TYPE_LABELS.get(value, value)


def _rating_label(my_rating: Any) -> str:
    try:
        score = float(my_rating)
    except (TypeError, ValueError):
        return "Nice"
    if score >= RATING_OUTSTANDING:
        return "Outstanding"
    if score >= RATING_GREAT:
        return "Great"
    return "Nice"


def build_game_object(game_json: dict) -> dict:
    """Game fields. Weekly custom_data is {"game": this object}."""
    return {
        "name": game_json.get("name"),
        "game_categories": _as_list(game_json.get("game_categories")),
        "min_players": _as_int(game_json.get("min_players")),
        "max_players": _as_int(game_json.get("max_players")),
        "publisher": game_json.get("distributor"),
        "image": game_json.get("image"),
        "original_price": _as_int(game_json.get("original_price")),
        "final_price": _as_int(game_json.get("final_price")),
        "discount_percent": _as_int(game_json.get("discount_percent")),
        "url": game_json.get("url"),
        "min_age": _as_int(game_json.get("min_age")),
        "my_rating": _as_int(game_json.get("my_rating")),
        "bgg_rating": game_json.get("bgg_rating"),
        "play_time_minutes": _as_int(game_json.get("play_time_minutes")),
        "complexity": game_json.get("complexity"),
        "game_mechanics": _as_list(game_json.get("game_mechanics")),
        "game_type": _map_game_type(game_json.get("game_type")),
    }


def build_email_payload(game_json: dict) -> dict:
    """Daily custom_data: rating, offer date, and the game object."""
    return {
        "rating": _rating_label(game_json.get("my_rating")),
        "offer_date": date.today().isoformat(),
        "game": build_game_object(game_json),
    }


def _send_email(template_id: str, custom_data: dict) -> Optional[dict]:
    """Send the given deal email template to the configured user."""
    validate_onesignal_env()
    external_id = os.getenv("MY_USER_EXTERNAL_ID")
    notification = Notification(
        app_id=app_id,
        template_id=template_id,
        include_aliases=IncludeAliases(external_id=[external_id] if external_id else []),
        target_channel="email",
        custom_data=custom_data,
    )
    with onesignal.ApiClient(configuration) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        try:
            api_response = api_instance.create_notification(notification)
            logger.info("OneSignal email sent: %s", api_response)
            return api_response
        except onesignal.ApiException as e:
            logger.error("OneSignal API error: %s", e)
            return None
        except AttributeError as e:
            if "'HTTPResponse' object has no attribute 'getheader'" in str(e):
                logger.debug("Ignoring OneSignal SDK compatibility issue: %s", e)
                return None
            raise
        except Exception as e:
            logger.warning("Unexpected error in OneSignal integration: %s", e)
            return None


def send_deal_email(game_json: dict) -> Optional[dict]:
    """Send the daily deal email. custom_data includes rating, offer_date, and game."""
    return _send_email(EMAIL_TEMPLATE_ID, build_email_payload(game_json))


def send_weekly_deal_email(game_json: dict) -> Optional[dict]:
    """Send the weekly deal email. custom_data is {"game": ...} only."""
    return _send_email(WEEKLY_EMAIL_TEMPLATE_ID, {"game": build_game_object(game_json)})
