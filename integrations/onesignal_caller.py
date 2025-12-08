import onesignal
from onesignal.api import default_api
from onesignal.model.custom_events_request import CustomEventsRequest
from onesignal.model.custom_event import CustomEvent
from onesignal.model.notification import Notification
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

load_dotenv()

# See configuration.py for a list of all supported configuration parameters.
# Some of the OneSignal endpoints require ORGANIZATION_API_KEY token for authorization, while others require REST_API_KEY.
# We recommend adding both of them in the configuration page so that you will not need to figure it out yourself.
configuration = onesignal.Configuration(
    rest_api_key = os.getenv("ONESIGNAL_API_KEY"), # App REST API key required for most endpoints
    organization_api_key = os.getenv("ONESIGNAL_ORGANIZATION_API_KEY") # Organization key is only required for creating new apps and other top-level endpoints
)

app_id = os.getenv("ONESIGNAL_APP_ID")

# Enter a context with an instance of the API client
def send_notification() -> dict:

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
            print(f"Error creating notification: {e}")
            return None

def send_custom_event(game_json: dict) -> dict:
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
            # Create custom events
            api_response = api_instance.create_custom_events(app_id, custom_events_request)
            print(api_response)
            return api_response
        except onesignal.ApiException as e:
            print("Exception when calling DefaultApi->create_custom_events: %s\n" % e)
            return None
        except AttributeError as e:
            # Ignore intermittent urllib3 compatibility issue: 'HTTPResponse' object has no attribute 'getheader'
            # This error occurs due to version incompatibility but doesn't affect functionality
            if "'HTTPResponse' object has no attribute 'getheader'" in str(e):
                print(f"Ignoring OneSignal SDK compatibility issue (functionality unaffected): {e}")
                return None
            else:
                # Re-raise if it's a different AttributeError
                raise
        except Exception as e:
            # Catch any other unexpected errors to prevent workflow failure
            print(f"Unexpected error in OneSignal integration (ignoring): {e}")
            return None
