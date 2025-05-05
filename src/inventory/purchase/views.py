# Django Imports
import django_filters
from django.db import transaction
from django_filters import FilterSet

# Rest Framework Imports
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from src.inventory.purchase.constants import PurchaseType

# Project Imports
from .models import InvPurchaseMain
from .permissions import PurchasePermission, PurchaseReturnPermission
from .serializers.common import (
    InvPurchaseListSerializer,
    InvPurchaseRetrieveSerializer,
)
from .serializers.purchase_return import InvPurchaseReturnCreateSerializer
from .serializers.purchase import InvPurchaseCreateSerializer


class FilterForInvPurchaseView(FilterSet):
    date = django_filters.DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = InvPurchaseMain
        fields = ["purchase_type", "date", "supplier", "bill_no", "purchase_no_full"]


class InvPurchaseViewset(ModelViewSet):
    queryset = InvPurchaseMain.objects.filter(
        purchase_type=PurchaseType.PURCHASE.value, is_archived=False
    )
    permission_classes = [PurchasePermission]
    filterset_class = FilterForInvPurchaseView
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    ordering_fields = ["id", "purchase_no"]
    search_fields = ["id", "purchase_no", "bill_no"]
    ordering = ["-purchase_no"]
    http_method_names = ["get", "options", "post", "head"]

    def get_serializer_class(self):
        serializer_class = InvPurchaseListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = InvPurchaseListSerializer
            else:
                serializer_class = InvPurchaseRetrieveSerializer

        if self.request.method == "POST":
            serializer_class = InvPurchaseCreateSerializer

        return serializer_class

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class InvPurchaseReturnView(ModelViewSet):
    queryset = InvPurchaseMain.objects.filter(
        purchase_type=PurchaseType.RETURN.value, is_archived=False
    )
    permission_classes = [PurchaseReturnPermission]
    filterset_class = FilterForInvPurchaseView
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    ordering_fields = ["id", "purchase_no"]
    search_fields = ["id", "purchase_no", "bill_no"]
    ordering = ["-purchase_no"]
    http_method_names = ["get", "options", "post", "head"]

    def get_serializer_class(self):
        serializer_class = InvPurchaseListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = InvPurchaseListSerializer
            else:
                serializer_class = InvPurchaseRetrieveSerializer

        if self.request.method == "POST":
            serializer_class = InvPurchaseReturnCreateSerializer

        return serializer_class

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
