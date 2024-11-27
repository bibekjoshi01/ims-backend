from typing import Dict, Union
from rest_framework import serializers

from src.core.constants import ThirdPartyApps
from src.user.oauth import AppleOAuth, GoogleOAuth
from src.user.models import User


class PublicUserSignUpSerializer(serializers.Serializer):
    third_party_app = serializers.ChoiceField(choices=ThirdPartyApps.choices())
    auth_token = serializers.CharField()

    def register_or_login_user(self, user_info: Dict) -> Dict[str, str | int]:
        try:
            registered_user: User = User.objects.get(email=user_info.get("email"))

            # Check if account status is active
            if not registered_user.is_active:
                raise serializers.ValidationError({"message": "Account Disabled. "})

            registered_user.is_email_verified = True
            registered_user.save()

            return {
                "uuid": registered_user.uuid,
                "tokens": registered_user.tokens,
                "full_name": registered_user.get_full_name
            }

        except User.DoesNotExist:
            return {}

    def validate(self, attrs) -> Dict[str, Union[str, int]]:
        provider = attrs.get("third_party_app", "")
        auth_token = attrs.get("auth_token", "")

        user_info = {}
        if provider == ThirdPartyApps.GOOGLE.value:
            user_info = GoogleOAuth.validate(auth_token)
        elif provider == ThirdPartyApps.APPLE.value:
            user_info = AppleOAuth.validate(auth_token)
        else:
            ...
            # TODO: Handle for other auth providers

        if user_info["type"] == "success":
            self.register_or_login_user(user_info)
        else:
            raise serializers.ValidationError({"message": "Unable to signup. Please try again."})

        return auth_token
