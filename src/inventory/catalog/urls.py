from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .listing_apis.views import (
    ProductCategoryForProductListAPIView,
    ProductUnitForProductListAPIView,
)
from .views import ProductCategoryViewSet, ProductViewSet

router = DefaultRouter(trailing_slash=False)


router.register("categories", ProductCategoryViewSet, basename="product-category")
router.register("products", ProductViewSet, basename="product")

urlpatterns = [
    path(
        "products/categories",
        ProductCategoryForProductListAPIView.as_view(),
        name="product-category-list",
    ),
    path(
        "products/units",
        ProductUnitForProductListAPIView.as_view(),
        name="product-unit-list",
    ),
    path("", include(router.urls)),
]
