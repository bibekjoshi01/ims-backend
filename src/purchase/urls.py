from rest_framework.routers import DefaultRouter
from django.urls import path, include

router = DefaultRouter()


from .views import PurchaseViewSet, PurchaseReturnViewSet


router.register("purchase", PurchaseViewSet, basename="purchase")
router.register("purchase-return", PurchaseReturnViewSet, basename="purchase-return")


urlpatterns = [path(""), path("", include(router.urls))]
