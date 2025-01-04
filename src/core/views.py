from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.viewsets import ModelViewSet

from .models import EmailConfig, OrganizationSetup, ThirdPartyCredential
from .permissions import (
    EmailConfigPermission,
    OrganizationSetupPermission,
    ThirdPartyCredentialPermission,
)
from .serializers import (
    EmailConfigCreateSerializer,
    EmailConfigListSerializer,
    EmailConfigPatchSerializer,
    EmailConfigRetrieveSerializer,
    OrganizationSetupCreateSerializer,
    OrganizationSetupListSerializer,
    OrganizationSetupPatchSerializer,
    OrganizationSetupRetrieveSerializer,
    ThirdPartyCredentialCreateSerializer,
    ThirdPartyCredentialListSerializer,
    ThirdPartyCredentialPatchSerializer,
    ThirdPartyCredentialRetrieveSerializer,
)


class OrganizationSetupViewSet(ModelViewSet):
    """Organization Setup ViewSet"""

    permission_classes = [OrganizationSetupPermission]
    queryset = OrganizationSetup.objects.filter(is_archived=False)
    http_method_names = ["get", "head", "options", "post", "patch"]

    def get_serializer_class(self):
        serializer_class = OrganizationSetupListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = OrganizationSetupListSerializer
            else:
                serializer_class = OrganizationSetupRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = OrganizationSetupCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = OrganizationSetupPatchSerializer

        return serializer_class


class ThirdPartyCredentialViewSet(ModelViewSet):
    """Third Party Credentials ViewSet"""

    permission_classes = [ThirdPartyCredentialPermission]
    queryset = ThirdPartyCredential.objects.filter(is_archived=False)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    serializer_class = ThirdPartyCredentialListSerializer
    filterset_fields = ["gateway"]
    search_fields = ["gateway"]
    ordering = ["-created_at"]
    ordering_fields = ["id", "created_at"]
    http_method_names = ["get", "head", "options", "post", "patch"]

    def get_serializer_class(self):
        serializer_class = ThirdPartyCredentialListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = ThirdPartyCredentialListSerializer
            else:
                serializer_class = ThirdPartyCredentialRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = ThirdPartyCredentialCreateSerializer
        if self.request.method == "PATCH":
            serializer_class = ThirdPartyCredentialPatchSerializer

        return serializer_class


class EmailConfigViewSet(ModelViewSet):
    """Email Config ViewSet"""

    permission_classes = [EmailConfigPermission]
    queryset = EmailConfig.objects.filter(is_archived=False)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    serializer_class = EmailConfigListSerializer
    filterset_fields = ["email_type"]
    search_fields = ["email_type", "default_from_email"]
    ordering = ["-created_at"]
    ordering_fields = ["id", "created_at"]
    http_method_names = ["get", "head", "options", "post", "patch"]

    def get_serializer_class(self):
        serializer_class = EmailConfigListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = EmailConfigListSerializer
            else:
                serializer_class = EmailConfigRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = EmailConfigCreateSerializer
        if self.request.method == "PATCH":
            serializer_class = EmailConfigPatchSerializer

        return serializer_class
