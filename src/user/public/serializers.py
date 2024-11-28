# Standard Library Imports
from typing import Dict, Union

# Django Core Imports
from django.conf import settings
from django.utils import timezone

# Rest Framework Imports
from rest_framework import serializers

# Custom Imports
from src.user.oauth import AuthTokenValidator, AuthProviders
from src.user.models import User
from .messages import ERROR_MESSAGES


class PublicUserSignInSerializer(serializers.Serializer):
    third_party_app = serializers.ChoiceField(choices=AuthProviders.choices())
    auth_token = serializers.CharField()

    def register_or_login_user(self, user_info: Dict) -> Dict[str, str | int]:
        """
        Registers a new user or logs in an existing one based on the third-party OAuth response.
        """
        try:
            user: User = User.objects.get(email=user_info["email"])

            # Check if account status is active
            if not user.is_active:
                raise serializers.ValidationError({"message": ERROR_MESSAGES["account_disabled"]})

            if not user.is_email_verified:
                user.is_email_verified = True

        except User.DoesNotExist:
            user = User.objects.create_public_user(
                auth_provider=user_info.get("provider"),
                username=user_info.get("email").split("@")[0],  # Generate username from email
                email=user_info.get("email"),
                password=settings.SOCIAL_SECRET,
                photo=user_info.get("photo"),
                first_name=user_info.get("first_name"),
                last_name=user_info.get("last_name")
            )

            user.created_by = user

        user.last_login = timezone.now()
        user.save()

        return {
            "uuid": user.uuid,
            "tokens": user.tokens,
            "full_name": user.full_name
        }

    def validate(self, attrs) -> Dict[str, Union[str, int]]:
        provider = attrs.get("third_party_app", "")
        auth_token = attrs.get("auth_token", "")

        user_info = AuthTokenValidator.validate(provider, auth_token)

        return self.register_or_login_user(user_info)
