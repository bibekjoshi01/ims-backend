from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path
from django.views.generic import TemplateView

from .schema import platform_docs_view, platform_schema_view

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
        path("api/docs/", platform_docs_view, name="platform-docs"),
        path("api/schema/", platform_schema_view, name="platform-schema"),
    ]
