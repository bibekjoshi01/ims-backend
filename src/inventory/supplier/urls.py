from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvSupplierViewSet

router = DefaultRouter(trailing_slash=False)


router.register("suppliers", InvSupplierViewSet, basename="inv-supplier")

urlpatterns = [
    path("", include(router.urls)),
]
