import django_filters
from django_filters.rest_framework import (
    DateFromToRangeFilter,
    DjangoFilterBackend,
    FilterSet,
)
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView

# Project Imports
from src.libs.pagination import CustomLimitOffsetPagination, CustomPageNumberPagination
from src.user.models import MainModule, Permission, PermissionCategory, Role
from src.user.permissions import RoleSetupPermission, UserSetupPermission

from .serializers import (
    MainModuleSerializer,
    RoleForUserSerializer,
    UserPermissionCategorySerializer,
    UserPermissionSerializer,
)


class FilterForMainModule(FilterSet):
    date = DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = MainModule
        fields = ["id", "date", "name"]


class MainModuleForRoleView(ListAPIView):
    """Main Module List API View"""

    permission_classes = [RoleSetupPermission]
    queryset = MainModule.objects.filter(is_active=True)
    serializer_class = MainModuleSerializer
    filterset_class = FilterForMainModule
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    http_method_names = ["get", "head", "options"]


class FilterForUserPermission(FilterSet):
    date = DateFromToRangeFilter(field_name="created_at")
    codename = django_filters.CharFilter()
    permission_category = django_filters.NumberFilter(field_name="permission_category")
    main_module = django_filters.NumberFilter(
        field_name="permission_category__main_module",
        label="Main Module",
    )

    class Meta:
        model = Permission
        fields = [
            "id",
            "date",
            "name",
            "codename",
            "permission_category",
            "main_module",
        ]


class UserPermissionForRoleView(ListAPIView):
    """User Permissions List View"""

    permission_classes = [RoleSetupPermission]
    pagination_class = CustomPageNumberPagination
    queryset = Permission.objects.filter(is_active=True)
    serializer_class = UserPermissionSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_class = FilterForUserPermission
    http_method_names = ["get", "head", "options"]
    search_fields = ["name", "codename", "codename"]
    ordering_fields = ["id", "name", "codename"]
    ordering = ["id"]


class FilterForUserPermissionCategory(FilterSet):
    date = DateFromToRangeFilter(field_name="created_at")
    main_module = django_filters.NumberFilter(field_name="main_module")

    class Meta:
        model = PermissionCategory
        fields = ["id", "date", "name", "codenamemain_module"]


class UserPermissionCategoryForRoleView(ListAPIView):
    """User Permission Category List View"""

    pagination_class = CustomLimitOffsetPagination
    permission_classes = [RoleSetupPermission]
    queryset = PermissionCategory.objects.filter(is_active=True)
    serializer_class = UserPermissionCategorySerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filterset_class = FilterForUserPermissionCategory
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
    http_method_names = ["get", "head", "options"]


class RoleForUserView(ListAPIView):
    permission_classes = [UserSetupPermission]
    queryset = Role.objects.filter(is_active=True, is_system_managed=False)
    serializer_class = RoleForUserSerializer
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    filter_fields = ["id", "name", "codename"]
    search_fields = ["id", "name"]
    ordering_fields = ["id", "name"]
    ordering = ["name"]
