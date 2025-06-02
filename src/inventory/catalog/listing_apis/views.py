from rest_framework import filters
from rest_framework.generics import ListAPIView

# Project Imports
from src.inventory.catalog.models import ProductCategory, ProductUnit
from src.inventory.catalog.permissions import ProductPermission

from .serializers import (
    ProductCategoryForProductListSerializer,
    ProductUnitForProductListSerializer,
)


class ProductCategoryForProductListAPIView(ListAPIView):
    permission_classes = [ProductPermission]
    queryset = ProductCategory.objects.filter(is_active=True)
    serializer_class = ProductCategoryForProductListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code"]
    http_method_names = ["get", "head", "options"]


class ProductUnitForProductListAPIView(ListAPIView):
    permission_classes = [ProductPermission]
    queryset = ProductUnit.objects.filter(is_active=True)
    serializer_class = ProductUnitForProductListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "short_form"]
    http_method_names = ["get", "head", "options"]
