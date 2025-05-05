from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import InvPurchaseViewset, InvPurchaseReturnView
from .listing_apis.views import (
    AdditionalChargeTypeForPurchaseView,
    PaymentMethodForPurchaseView,
    ProductCategoryForPurchaseView,
    ItemForPurchaseView,
    PurchaseDetailForPurchaseReturnView,
    PurchaseForPurchaseReturnView,
    SupplierForPurchaseView,
    PurchaseDetailForPurchaseView,
)

router = DefaultRouter(trailing_slash=False)

router.register("purchases", InvPurchaseViewset, basename="inv-purchase")
router.register(
    "purchase-returns", InvPurchaseReturnView, basename="inv-purchase-return"
)

urlpatterns = [
    # path("purchase/product-categories", ProductCategoryForPurchaseView.as_view()),
    # path("purchase/product-variants", ProductVariantForPurchaseView.as_view()),
    # path("purchase/payment-methods", PaymentMethodForPurchaseView.as_view()),
    # path("purchase/suppliers", SupplierForPurchaseView.as_view()),
    # path(
    #     "purchase/additional-charge-types",
    #     AdditionalChargeTypeForPurchaseView.as_view(),
    # ),
    # path(
    #     "purchase/purchase-detail/<int:id>",
    #     PurchaseDetailForPurchaseView.as_view(),
    # ),
    # path("purchase-return/purchases", PurchaseForPurchaseReturnView.as_view()),
    # path(
    #     "purchase-return/purchase-details",
    #     PurchaseDetailForPurchaseReturnView.as_view(),
    # ),
    path("", include(router.urls)),
]
