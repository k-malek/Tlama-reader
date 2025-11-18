import onesignal
from onesignal.api import default_api
from onesignal.model.notification import Notification
from dotenv import load_dotenv
import os

load_dotenv()

# See configuration.py for a list of all supported configuration parameters.
# Some of the OneSignal endpoints require ORGANIZATION_API_KEY token for authorization, while others require REST_API_KEY.
# We recommend adding both of them in the configuration page so that you will not need to figure it out yourself.
configuration = onesignal.Configuration(
    rest_api_key = os.getenv("ONESIGNAL_API_KEY"), # App REST API key required for most endpoints
    organization_api_key = os.getenv("ONESIGNAL_ORGANIZATION_API_KEY") # Organization key is only required for creating new apps and other top-level endpoints
)

# Enter a context with an instance of the API client
def create_notification() -> dict:

    notification = Notification(
        app_id=os.getenv("ONESIGNAL_APP_ID"),
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
