# Django Imports
from django_filters import FilterSet
from django.db import transaction
import django_filters

# Rest Framework Imports
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

# Project Imports
from src.purchase.constants import PurchaseType
from .models import Purchase
from .permissions import PurchasePermission, PurchaseReturnPermission
from .serializers import (
    PurchaseListSerializer,
    PurchaseRetrieveSerializer,
    PurchaseCreateSerializer,
)


class FilterForPurchase(FilterSet):
    date = django_filters.DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = Purchase
        fields = ["date", "pay_type", "purchase_no", "supplier", "bill_no"]


class PurchaseViewSet(ModelViewSet):
    permission_classes = [PurchasePermission]
    queryset = Purchase.objects.filter(
        is_archived=False, purchase_type=PurchaseType.PURCHASE.value
    )
    filterset_class = FilterForPurchase
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["purchase_no", "supplier__name", "bill_no"]
    ordering_fields = [
        "id",
        "bill_no",
        "grand_total",
        "sub_total",
        "bill_date",
        "due_date",
    ]
    ordering = ["-id"]
    http_method_names = ["get", "options", "head", "post", "patch", "delete"]

    def get_serializer_class(self):
        serializer_class = PurchaseListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = PurchaseListSerializer
            else:
                serializer_class = PurchaseRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = PurchaseCreateSerializer

        return serializer_class

    @transaction.atomic
    def perform_create(self, serializer):
        return super().perform_create(serializer)


class FilterForPurchaseReturn(FilterSet):
    date = django_filters.DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = Purchase
        fields = ["date", "pay_type", "purchase_no", "supplier", "bill_no"]


class PurchaseReturnViewSet(ModelViewSet):
    permission_classes = [PurchaseReturnPermission]
    queryset = Purchase.objects.filter(
        is_archived=False, purchase_type=PurchaseType.RETURN.value
    )
    filterset_class = FilterForPurchaseReturn
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["purchase_no", "supplier__name", "bill_no"]
    ordering_fields = [
        "id",
        "bill_no",
        "grand_total",
        "sub_total",
        "bill_date",
        "due_date",
    ]
    ordering = ["-id"]
    http_method_names = ["get", "options", "head", "post", "patch", "delete"]

    def get_serializer_class(self):
        serializer_class = PurchaseListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = PurchaseListSerializer
            else:
                serializer_class = PurchaseRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = PurchaseCreateSerializer

        return serializer_class

    @transaction.atomic
    def perform_create(self, serializer):
        return super().perform_create(serializer)
