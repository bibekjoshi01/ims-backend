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

from .messages import CUSTOMER_DELETE_SUCCESS
from .models import Customer
from .permissions import CustomerPermission
from .serializers import (
    CustomerCreateSerializer,
    CustomerListSerializer,
    CustomerPatchSerializer,
    CustomerRetrieveSerializer,
)


class FilterForCustomer(FilterSet):
    class Meta:
        model = Customer
        fields = [
            "id",
            "full_name",
            "email",
            "phone_no",
            "alt_phone_no",
            "customer_no",
            "is_person",
        ]


class CustomerViewSet(ModelViewSet):
    permission_classes = [CustomerPermission]
    queryset = Customer.objects.filter(is_archived=False)
    filterset_class = FilterForCustomer
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["full_name", "email", "phone_no", "alt_phone_no"]
    ordering_fields = ["id", "full_name", "email", "is_active", "is_person"]
    ordering = ["-id"]
    http_method_names = ["get", "options", "head", "post", "patch", "delete"]

    def get_serializer_class(self):
        serializer_class = CustomerListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = CustomerListSerializer
            else:
                serializer_class = CustomerRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = CustomerCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = CustomerPatchSerializer

        return serializer_class

    def perform_destroy(self, instance: Customer):
        instance.is_archived = True
        instance.updated_by = get_user_by_request(self.request)
        instance.save(update_fields=["is_archived", "updated_by"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"id": instance.id, "message": CUSTOMER_DELETE_SUCCESS},
            status=status.HTTP_200_OK,
        )
