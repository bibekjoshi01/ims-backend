# Third Party Imports
import requests
from requests.exceptions import RequestException

# Custom Imports
from django.conf import settings
from .constants import UserInfo


class GoogleOAuth:
    """
    Google OAuth provider class for validating authentication tokens
    and retrieving user information.
    """
    TOKEN_INFO_API = "https://oauth2.googleapis.com/tokeninfo"
    USER_INFO_API = "https://www.googleapis.com/oauth2/v3/userinfo"

    @classmethod
    def validate(cls, auth_token: str) -> UserInfo | Dict:
        """
        Validates an authentication token and retrieves user information.

        Args:
            auth_token (str): The authentication token to validate.

        Returns:
            dict: A dictionary containing user information or an error message.

        Raises:
            ValueError: If the auth token is missing or invalid.
            RequestException: If there's an issue with the API request.
            KeyError: If the expected fields are missing in the API response.
        """
        if not cls.TOKEN_INFO_API or not cls.USER_INFO_API:
            raise NotImplementedError("Subclasses must define token_info_api and user_info_api.")

        try:
            # Validate the token with the provider's token API
            token_response = requests.get(
                cls.TOKEN_INFO_API, params={"access_token": auth_token}, timeout=10
            )
            token_response.raise_for_status()
            token_info = token_response.json()

            # Ensure the token is valid for this client
            if token_info.get("aud") != settings.GOOGLE_CLIENT_ID:
                return {"type": "error", "message": "Invalid Google Client ID"}

            # Retrieve user information
            user_response = requests.get(
                cls.USER_INFO_API, params={"access_token": auth_token}, timeout=10
            )
            user_response.raise_for_status()
            user_info = user_response.json()

            # Format and return user info
            return {
                "type": "success",
                "first_name": user_info.get("given_name", ""),
                "last_name": user_info.get("family_name", ""),
                "full_name": user_info.get("name", ""),
                "photo": user_info.get("picture", None),
                "email": user_info.get("email"),
            }

        except RequestException as err:
            return {"type": "error", "message": f"API request failed: {err}"}
        except KeyError as err:
            return {"type": "error", "message": f"Missing field in response: {err}"}
        except Exception as err:
            return {"type": "error", "message": f"Unexpected error: {err}"}
