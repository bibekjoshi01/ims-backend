from typing import Any

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Platform
platform_schema_view = SpectacularAPIView.as_view(urlconf="config.platform_urls")
platform_docs_view = SpectacularSwaggerView.as_view(url_name="platform-schema")


# Tenant
class CustomTenantSpectacularSwaggerView(SpectacularSwaggerView):
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        from django.shortcuts import redirect
        from rest_framework.reverse import reverse

        response = super().dispatch(request, *args, **kwargs)
        if response.status_code == 401 or not request.user.is_authenticated:
            # Redirect the user to the login page if not authenticated
            return redirect(reverse("rest_framework:login") + f"?next={request.path}")
        return response


class CustomTenantSpectacularAPIView(SpectacularAPIView):
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        from django.shortcuts import redirect
        from rest_framework.reverse import reverse

        response = super().dispatch(request, *args, **kwargs)
        if response.status_code == 401 or not request.user.is_authenticated:
            # Redirect the user to the login page if not authenticated
            return redirect(reverse("rest_framework:login") + f"?next={request.path}")
        return response
