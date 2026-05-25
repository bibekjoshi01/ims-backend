from datetime import datetime, timedelta

import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import PlatformUser


class PlatformJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get("Authorization")

        if not auth:
            return None

        try:
            prefix, token = auth.split(" ")
            if prefix.lower() != "bearer":
                return None
        except Exception:
            return None

        try:
            payload = decode_token(token)
            user = PlatformUser.objects.get(id=payload["user_id"])
        except Exception as err:
            raise AuthenticationFailed("Invalid token") from err

        return (user, None)


def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.now() + timedelta(minutes=60),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


def login_user(username, password):
    try:
        user = PlatformUser.objects.get(username=username)
    except PlatformUser.DoesNotExist:
        return None, "Invalid credentials"

    if not user.check_password(password):
        return None, "Invalid credentials"

    if not user.is_active:
        return None, "User inactive"

    token = generate_token(user.id)

    return {
        "token": token,
        "user_id": user.id,
        "username": user.username,
    }, None
