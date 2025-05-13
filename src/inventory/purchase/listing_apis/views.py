from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView, RetrieveAPIView

from src.inventory.catalog.models import Item, ItemCategory
from src.inventory.purchase.constants import PurchaseType
from src.inventory.supplier.models import InvSupplier
from src.core.models import AdditionalChargeType, PaymentMethod
from src.inventory.purchase.models import InvPurchaseDetail, InvPurchaseMain
from ..permissions import PurchasePermission
from .serializers import (
    ItemCategoryForPurchaseSerializer,
    ItemForPurchaseSerializer,
    PaymentMethodForPurchaseSerializer,
    PurchaseDetailForPurchaseSerializer,
    PurchaseForPurchaseReturnSerializer,
    SupplierForPurchaseSerializer,
    AdditionalChargeTypeForPurchaseSerializer,
)


class ProductCategoryForPurchaseView(ListAPIView):
    permission_classes = [PurchasePermission]
    queryset = ItemCategory.objects.filter(is_active=True)
    serializer_class = ItemCategoryForPurchaseSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "name"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["name"]


class ItemForPurchaseView(ListAPIView):
    permission_classes = [PurchasePermission]
    queryset = Item.objects.filter(is_active=True)
    serializer_class = ItemForPurchaseSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "name"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["name"]


class PaymentMethodForPurchaseView(ListAPIView):
    permission_classes = [PurchasePermission]
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodForPurchaseSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "name"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["name"]


class SupplierForPurchaseView(ListAPIView):
    permission_classes = [PurchasePermission]
    queryset = InvSupplier.objects.filter(user__is_active=True)
    serializer_class = SupplierForPurchaseSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "user__first_name", "user__middle_name", "user__last_name"]
    search_fields = [
        "user__first_name",
        "user__middle_name",
        "user__last_name",
        "user__pan_no",
        "user__mobile_no",
        "user__phone_no",
    ]
    ordering_fields = ["id", "user__first_name", "user__middle_name", "user__last_name"]
    ordering = ["user__first_name", "user__middle_name", "user__last_name"]


class AdditionalChargeTypeForPurchaseView(ListAPIView):
    permission_classes = [PurchasePermission]
    queryset = AdditionalChargeType.objects.filter(is_active=True)
    serializer_class = AdditionalChargeTypeForPurchaseSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "name"]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["name"]


class PurchaseDetailForPurchaseView(RetrieveAPIView):
    permission_classes = [PurchasePermission]
    queryset = InvPurchaseDetail.objects.all()
    serializer_class = PurchaseDetailForPurchaseSerializer
    lookup_field = "id"


class PurchaseForPurchaseReturnView(ListAPIView):
    permission_classes = [PurchasePermission]
    queryset = InvPurchaseMain.objects.filter(purchase_type=PurchaseType.PURCHASE.value)
    serializer_class = PurchaseForPurchaseReturnSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "supplier"]
    search_fields = ["supplier__user__get_full_name", "bill_no", "purchase_no_full"]
    ordering_fields = ["id", "purchase_no_full", "created_date_ad"]
    ordering = ["-purchase_no_full"]


class PurchaseDetailForPurchaseReturnView(ListAPIView):
    permission_classes = [PurchasePermission]
    queryset = InvPurchaseDetail.objects.filter(
        purchase_main__purchase_type=PurchaseType.PURCHASE.value,
        ref_purchase_detail__isnull=True,
    )
    serializer_class = PurchaseDetailForPurchaseSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "purchase_main"]
    search_fields = ["id", "product_variant__name"]
    ordering_fields = ["id", "product_variant__name"]
    ordering = ["product_variant__name"]
