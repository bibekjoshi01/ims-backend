from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.shortcuts import get_object_or_404
from django_tenants.utils import schema_context
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

# Project Imports
from control_plane.auth import PlatformJWTAuthentication, login_user
from tenants.models import Tenant

from .permissions import IsPlatformUser
from .serializers import (
    TenantCreateSerializer,
    TenantListSerializer,
    TenantPatchSerializer,
    TenantRetrieveSerializer,
    TenantUserCreateSerializer,
    TenantUserListSerializer,
    TenantUserPatchSerializer,
    TenantUserRetrieveSerializer,
)

User = get_user_model()


class TenantViewset(ModelViewSet):
    permission_classes = [IsPlatformUser]
    authentication_classes = [PlatformJWTAuthentication]
    serializer_class = TenantListSerializer
    queryset = Tenant.objects.exclude(schema_name="public")
    http_method_names = ["head", "options", "get", "post", "patch"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == "list":
                return TenantListSerializer
            if self.action == "retrieve":
                return TenantRetrieveSerializer
        if self.request.method == "POST":
            return TenantCreateSerializer
        if self.request.method == "PATCH":
            return TenantPatchSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            tenant = serializer.save()
        out_serializer = TenantRetrieveSerializer(tenant, context={"request": request})
        headers = self.get_success_headers(out_serializer.data)

        return Response(out_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        tenant = self.get_object()
        tenant.activate()
        return Response({"message": "Account activate successfully."}, status=status.HTTP_200_OK)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        tenant = self.get_object()
        tenant.suspend()
        return Response({"message": "Account deactivate successfully."}, status=status.HTTP_200_OK)


class TenantUserViewset(ModelViewSet):
    permission_classes = [IsPlatformUser]
    authentication_classes = [PlatformJWTAuthentication]
    http_method_names = ["get", "post", "patch", "head", "options"]

    serializer_class = TenantUserListSerializer  # default fallback

    def get_tenant(self):
        if not hasattr(self, "_tenant"):
            self._tenant = get_object_or_404(
                Tenant.objects.exclude(schema_name="public"),
                id=self.kwargs.get("client_id"),
            )
        return self._tenant

    def get_queryset(self):
        tenant = self.get_tenant()
        connection.set_schema(tenant.schema_name)

        with schema_context(tenant.schema_name):
            return User.objects.filter(is_staff=True)

    def get_serializer_class(self):
        if self.action == "list":
            return TenantUserListSerializer
        if self.action == "retrieve":
            return TenantUserRetrieveSerializer
        if self.action == "create":
            return TenantUserCreateSerializer
        if self.action in ["update", "partial_update"]:
            return TenantUserPatchSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        tenant = self.get_tenant()

        with schema_context(tenant.schema_name):
            serializer.save()

    def perform_update(self, serializer):
        tenant = self.get_tenant()

        with schema_context(tenant.schema_name):
            serializer.save()


class LoginAPIView(CreateAPIView):
    authentication_classes = [PlatformJWTAuthentication]
    permission_classes = [AllowAny]

    def create(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        data, error = login_user(email, password)

        if error:
            return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)
