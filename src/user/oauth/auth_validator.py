from typing import Dict

from rest_framework.exceptions import ValidationError

from .constants import AuthProviders, UserInfo
from .messages import ERROR_MESSAGES
from . import GoogleOAuth, AppleOAuth


class AuthTokenValidator:
    """
    Token validator for third-party providers
    """

    provider_class_map = {
        "GOOGLE": GoogleOAuth,
        "APPLE": AppleOAuth
    }

    @staticmethod
    def validate(provider: str, token: str) -> UserInfo:
        try:
            if provider not in AuthProviders.choices():
                raise ValidationError({"message": ERROR_MESSAGES["provider_not_supported"]})

            auth_provider = AuthTokenValidator.provider_class_map[provider]
            user_info = auth_provider.validate(token)

            if user_info.get("type") != "success":
                raise ValidationError({"message": ERROR_MESSAGES["signin_failed"]})

            return user_info

        except ValueError as err:
            raise ValidationError({"message": str(err)})
        except AttributeError:
            raise ValidationError({"message": ERROR_MESSAGES["provider_not_supported"]})
        except Exception as err:
            raise ValidationError({"message": str(err)})
