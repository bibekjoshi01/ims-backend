# Django Imports
import django_filters
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters.filterset import FilterSet

# Rest Framework Imports
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework import status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

# Project Imports
from src.libs.utils import set_binary_files_null_if_empty
from src.user.constants import SYSTEM_USER_ROLE
from .messages import (
    USER_ARCHIVED,
    USER_NOT_FOUND,
    USER_ROLE_ARCHIVED,
    USER_ROLE_NOT_FOUND,
)
from .models import Role, User
from .permissions import RoleSetupPermission, UserSetupPermission
from .serializers import (
    RoleCreateSerializer,
    RoleListSerializer,
    RolePatchSerializer,
    RoleRetrieveSerializer,
    UserListSerializer,
    UserPatchSerializer,
    UserRegisterSerializer,
    UserRetrieveSerializer,
)

# User Role Setup


class FilterForRoleViewset(FilterSet):
    """Filters For User Role"""

    date = django_filters.DateFromToRangeFilter(field_name="created_at")
    name = django_filters.CharFilter(lookup_expr="iexact")
    codename = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Role
        fields = ["id", "date", "name", "codename", "is_active"]


class RoleViewSet(ModelViewSet):
    """
    ViewSet for managing CRUD operations for Role.
    """

    permission_classes = [RoleSetupPermission]
    queryset = Role.objects.filter(is_archived=False, is_system_managed=False)
    serializer_class = RoleListSerializer
    filterset_class = FilterForRoleViewset
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["name", "codename"]
    ordering = ["-created_at"]
    ordering_fields = ["created_at", "codename"]
    http_method_names = ["get", "head", "options", "post", "patch"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = RoleListSerializer
            else:
                serializer_class = RoleRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = RoleCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = RolePatchSerializer

        return serializer_class


class RoleArchiveView(generics.DestroyAPIView):
    """User Role Archive View"""

    permission_classes = [RoleSetupPermission]
    lookup_url_kwarg = "role_id"
    lookup_field = "id"
    queryset = Role.objects.filter(is_archived=False, is_system_managed=False)

    def perform_destroy(self, instance):
        instance.is_archived = True
        instance.updated_at = timezone.now()
        instance.save()

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        response.data = {"message": USER_ROLE_ARCHIVED}
        response.status_code = status.HTTP_204_NO_CONTENT
        return response


# User Setup


class FilterForUserViewSet(FilterSet):
    """Filters For User ViewSet"""

    username = django_filters.CharFilter(lookup_expr="iexact")
    date = django_filters.DateFromToRangeFilter(field_name="date_joined")

    class Meta:
        model = User
        fields = ["id", "username", "email", "phone_no", "roles", "date"]


class UserViewSet(ModelViewSet):
    """
    ViewSet for managing CRUD operations for User.
    """

    permission_classes = [UserSetupPermission]
    filterset_class = FilterForUserViewSet
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["phone_no", "username", "email", "first_name", "last_name"]
    ordering_fields = ["-id", "first_name"]
    http_method_names = ["options", "head", "get", "patch", "post"]

    def get_queryset(self):
        system_user_role = get_object_or_404(Role, codename=SYSTEM_USER_ROLE)
        return User.objects.filter(
            is_superuser=False,
            is_staff=False,
            roles__id=system_user_role.id,
            is_archived=False,
        )

    def get_serializer_class(self):
        serializer_class = UserListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = UserListSerializer
            else:
                serializer_class = UserRetrieveSerializer

        if self.request.method == "POST":
            serializer_class = UserRegisterSerializer
        elif self.request.method == "PATCH":
            serializer_class = UserPatchSerializer
        return serializer_class

    def create(self, request, *args, **kwargs):
        # set blank file fields to None/null
        file_fields = ["photo"]
        if file_fields:
            set_binary_files_null_if_empty(file_fields, request.data)

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # set blank file fields to None/null
        file_fields = ["photo"]
        if file_fields:
            set_binary_files_null_if_empty(file_fields, request.data)

        return super().update(request, *args, **kwargs)


class UserArchiveView(generics.DestroyAPIView):
    """User Archive View"""

    permission_classes = [UserSetupPermission]
    lookup_url_kwarg = "user_id"
    lookup_field = "id"
    queryset = User.objects.filter(is_archived=False)

    def perform_destroy(self, instance):
        instance.is_archived = True
        instance.updated_at = timezone.now()
        instance.save()

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        response.data = {"message": USER_ARCHIVED}
        response.status_code = status.HTTP_204_NO_CONTENT
        return response