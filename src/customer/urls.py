from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CustomerViewSet

router = DefaultRouter(trailing_slash=False)


router.register("customers", CustomerViewSet, basename="customer")

urlpatterns = [
    path("", include(router.urls)),
]
