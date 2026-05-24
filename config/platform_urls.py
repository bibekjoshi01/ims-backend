from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic import TemplateView

from .schema import CustomPlatformSpectacularAPIView, CustomPlatformSpectacularSwaggerView

urlpatterns = [
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("api/tenant-mod/", include("tenants.urls")),
]

if settings.DEBUG:
    # Static file serving when using Gunicorn + Uvicorn for local web socket development
    urlpatterns += staticfiles_urlpatterns()

    # API URLS
    urlpatterns += [
        # PLATFORM DOCS
        path("api/schema/", CustomPlatformSpectacularAPIView.as_view(), name="api-schema"),
        path(
            "api/docs/",
            CustomPlatformSpectacularSwaggerView.as_view(url_name="api-schema"),
            name="swagger-ui",
        ),
    ]
