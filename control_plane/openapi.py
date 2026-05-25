from drf_spectacular.extensions import OpenApiAuthenticationExtension

from .auth import PlatformJWTAuthentication


class PlatformJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = PlatformJWTAuthentication
    name = "PlatformJWTAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
