import django_filters
from django.db import transaction
from django_filters import FilterSet

# Rest Framework Imports
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

# Project Imports
from .models import InvSupplier
from .permissions import InvSupplierPermission
from .serializers import (
    InvSupplierListSerializer,
    InvSupplierRetrieveSerializer,
    InvSupplierPatchSerializer,
    InvSupplierCreateSerializer,
)


class FilterForInvSupplier(FilterSet):
    name = django_filters.CharFilter(
        field_name="user__first_name", lookup_expr="iexact", label="Full Name"
    )
    email = django_filters.CharFilter(
        field_name="user__email", lookup_expr="iexact", label="Email"
    )
    phone_no = django_filters.CharFilter(
        field_name="user__phone_no", lookup_expr="iexact", label="Phone No"
    )

    class Meta:
        model = InvSupplier
        fields = ["id", "name", "email", "phone_no"]


class InvSupplierViewSet(ModelViewSet):
    permission_classes = [InvSupplierPermission]
    queryset = InvSupplier.objects.filter(is_archived=False)
    filterset_class = FilterForInvSupplier
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = [
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone_no",
    ]
    ordering_fields = ["id", "user__first_name", "user__email"]
    ordering = ["-id"]
    http_method_names = ["get", "options", "head", "post", "patch"]

    def get_serializer_class(self):
        serializer_class = InvSupplierListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = InvSupplierListSerializer
            else:
                serializer_class = InvSupplierRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = InvSupplierCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = InvSupplierPatchSerializer

        return serializer_class

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
