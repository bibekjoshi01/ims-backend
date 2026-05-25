from control_plane.auth import PLATFORM_JWT_COOKIE, decode_token
from control_plane.models import PlatformUser


class PlatformUserJWTMiddleware:
    """
    Attach the platform admin user stored in the JWT cookie to each request.

    Dashboard views can then rely on `request.platform_user` without session
    state while still keeping the server-rendered shell protected.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.platform_user = None

        token = request.COOKIES.get(PLATFORM_JWT_COOKIE)
        if not token:
            return self.get_response(request)

        try:
            payload = decode_token(token)
            platform_user = PlatformUser.objects.get(pk=payload["user_id"])
        except Exception:
            return self.get_response(request)

        if platform_user.is_active and platform_user.is_platform_admin:
            request.platform_user = platform_user

        return self.get_response(request)
