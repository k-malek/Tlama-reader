import logging
import os
from datetime import datetime, timezone
from typing import Optional

import onesignal

from config import validate_onesignal_env
from onesignal.api import default_api
from onesignal.model.custom_event import CustomEvent
from onesignal.model.custom_events_request import CustomEventsRequest
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

def send_notification() -> Optional[dict]:

    notification = Notification(
        app_id=app_id,
        template_id="7b63e1a9-3765-4bf2-b156-91293565aa8c",
        included_segments=["Android Test"]
    )
    with onesignal.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        
        try:
            api_response = api_instance.create_notification(notification)
            return api_response
        except Exception as e:
            logger.error("Error creating notification: %s", e)
            return None

def send_custom_event(game_json: dict) -> Optional[dict]:
    validate_onesignal_env()
    with onesignal.ApiClient(configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        custom_events_request = CustomEventsRequest(
            events=[
                CustomEvent(
                    name="game_data",
                    external_id=os.getenv("MY_USER_EXTERNAL_ID"),
                    onesignal_id=os.getenv("MY_USER_ONESIGNAL_ID"),
                    timestamp=datetime.now(timezone.utc),
                    payload=game_json,
                ),
            ],
        )

        # example passing only required values which don't have defaults set
        try:
            api_response = api_instance.create_custom_events(app_id, custom_events_request)
            logger.info("OneSignal custom event sent: %s", api_response)
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
