from rest_framework.generics import ListAPIView
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from ..permissions import InvSupplierPermission
from src.core_app.models import District, TaxGroup
from .serializers import (
    DistrictListSerializerForSupplier,
    TaxGroupListSerializerForSupplier,
)


"""Tax Group List View"""


class FilterForTaxGroupListAPIViewForSupplier(FilterSet):
    class Meta:
        model = TaxGroup
        fields = ["name"]


class TaxGroupListAPIViewForSupplier(ListAPIView):
    permission_classes = [InvSupplierPermission]
    queryset = TaxGroup.objects.filter(is_active=True)
    serializer_class = TaxGroupListSerializerForSupplier
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    filterset_class = FilterForTaxGroupListAPIViewForSupplier
    ordering = ["-id"]
    search_fields = ["name"]


"""District List View"""


class FilterForDistrictListAPIViewForSupplier(FilterSet):
    class Meta:
        model = District
        fields = ["province", "name"]


class DistrictsListAPIViewForSupplier(ListAPIView):
    permission_classes = [InvSupplierPermission]
    queryset = District.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    serializer_class = DistrictListSerializerForSupplier
    filterset_class = FilterForDistrictListAPIViewForSupplier
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
