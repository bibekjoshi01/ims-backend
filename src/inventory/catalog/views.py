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

from .messages import CATEGORY_DELETE_SUCCESS, PRODUCT_DELETE_SUCCESS
from .models import Product, ProductCategory
from .permissions import ProductCategoryPermission, ProductPermission
from .serializers import (
    ProductCategoryCreateSerializer,
    ProductCategoryListSerializer,
    ProductCategoryPatchSerializer,
    ProductCategoryRetrieveSerializer,
    ProductCreateSerializer,
    ProductListSerializer,
    ProductPatchSerializer,
    ProductRetrieveSerializer,
)

# ------------------------------------------------------------------------
# Product Category
# ------------------------------------------------------------------------


class FilterForProductCategory(FilterSet):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "code"]


class ProductCategoryViewSet(ModelViewSet):
    permission_classes = [ProductCategoryPermission]
    queryset = ProductCategory.objects.filter(is_archived=False)
    filterset_class = FilterForProductCategory
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["name", "code"]
    ordering_fields = ["id", "name", "code"]
    ordering = ["-id"]
    http_method_names = ["get", "options", "head", "post", "patch", "delete"]

    def get_serializer_class(self):
        serializer_class = ProductCategoryListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = ProductCategoryListSerializer
            else:
                serializer_class = ProductCategoryRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = ProductCategoryCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = ProductCategoryPatchSerializer

        return serializer_class

    def perform_destroy(self, instance):
        instance.is_archived = True
        instance.updated_by = get_user_by_request(self.request)
        instance.save(update_fields=["is_archived", "updated_by"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"id": instance.id, "message": CATEGORY_DELETE_SUCCESS},
            status=status.HTTP_200_OK,
        )


# ------------------------------------------------------------------------
# Product
# ------------------------------------------------------------------------


class FilterForProduct(FilterSet):
    class Meta:
        model = Product
        fields = ["id", "sku", "category"]


class ProductViewSet(ModelViewSet):
    permission_classes = [ProductPermission]
    queryset = Product.objects.filter(is_archived=False)
    filterset_class = FilterForProduct
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["name", "sku", "barcode"]
    ordering_fields = ["id", "name", "sku", "selling_price", "stock_alert_qty"]
    ordering = ["-id"]
    http_method_names = ["get", "options", "head", "post", "patch", "delete"]

    def get_serializer_class(self):
        serializer_class = ProductListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = ProductListSerializer
            else:
                serializer_class = ProductRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = ProductCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = ProductPatchSerializer

        return serializer_class

    def perform_destroy(self, instance):
        instance.is_archived = True
        instance.updated_by = get_user_by_request(self.request)
        instance.save(update_fields=["is_archived", "updated_by"])

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"id": instance.id, "message": PRODUCT_DELETE_SUCCESS},
            status=status.HTTP_200_OK,
        )
