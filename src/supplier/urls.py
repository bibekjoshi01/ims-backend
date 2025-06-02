from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SupplierViewSet

router = DefaultRouter(trailing_slash=False)


router.register("suppliers", SupplierViewSet, basename="supplier")

urlpatterns = [
    path("", include(router.urls)),
]
