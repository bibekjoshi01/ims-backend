from django.urls import path
from rest_framework.routers import DefaultRouter

from control_plane.views import TenantUserViewset, TenantViewset

router = DefaultRouter(trailing_slash=False)

router.register("clients", TenantViewset)

urlpatterns = [
    path(
        "clients/<int:client_id>/users",
        TenantUserViewset.as_view({"get": "list", "post": "create"}),
    ),
    path(
        "clients/<int:client_id>/users/<int:pk>",
        TenantUserViewset.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "put": "update",
                "delete": "destroy",
            }
        ),
        name="tenant-user-detail",
    ),
] + router.urls
