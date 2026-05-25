from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import PlatformUser


class PlatformAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get("Authorization")

        if not token:
            return None

        token = token.replace("Bearer ", "")

        user = PlatformUser.objects.filter(auth_token=token).first()

        if not user:
            raise AuthenticationFailed("Invalid token")

        return (user, None)
