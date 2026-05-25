from rest_framework.permissions import BasePermission


class IsPlatformUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user:
            return False

        # must be authenticated via PlatformJWTAuthentication
        if not hasattr(user, "username"):
            return False

        if hasattr(user, "is_active") and not user.is_active:
            return False

        if hasattr(user, "is_platform_admin") and not user.is_platform_admin:
            return False

        return True
