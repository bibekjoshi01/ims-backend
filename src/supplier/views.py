# Django Imports
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

# Rest Framework Imports
from rest_framework.viewsets import ModelViewSet

# Project Imports
from src.libs.get_context import get_user_by_request

from .messages import SUPPLIER_DELETE_SUCCESS
from .models import Supplier
from .permissions import SupplierPermission
from .serializers import (
    SupplierCreateSerializer,
    SupplierListSerializer,
    SupplierPatchSerializer,
    SupplierRetrieveSerializer,
)


class FilterForSupplier(FilterSet):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "email",
            "phone_no",
            "alt_phone_no",
            "country",
            "is_active",
            "website",
        ]


class SupplierViewSet(ModelViewSet):
    permission_classes = [SupplierPermission]
    queryset = Supplier.objects.filter(is_archived=False)
    filterset_class = FilterForSupplier
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["name", "email", "contact_person", "phone_no", "alt_phone_no"]
    ordering_fields = ["id", "name", "contact_person", "email"]
    ordering = ["-id"]
    http_method_names = ["get", "options", "head", "post", "patch", "delete"]

    def get_serializer_class(self):
        serializer_class = SupplierListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = SupplierListSerializer
            else:
                serializer_class = SupplierRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = SupplierCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = SupplierPatchSerializer

        return serializer_class

    def perform_destroy(self, instance):
        instance.is_archived = True
        instance.updated_by = get_user_by_request(self.request)
        instance.save(update_fields=["is_archived", "updated_by"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"id": instance.id, "message": SUPPLIER_DELETE_SUCCESS},
            status=status.HTTP_200_OK,
        )
