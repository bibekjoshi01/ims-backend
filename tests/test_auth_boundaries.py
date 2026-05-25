from datetime import UTC, datetime, timedelta

import jwt
from django.conf import settings
from django.test import TestCase, override_settings
from django_tenants.utils import schema_context
from rest_framework.test import APIRequestFactory

from control_plane.auth import generate_token
from control_plane.models import PlatformUser
from control_plane.views import TenantViewset, _tenant_user_queryset
from src.user.models import User
from tenants.models import Tenant


@override_settings(
    ALLOWED_HOSTS=["localhost", "testserver"],
    SECRET_KEY="test-secret-key-test-secret-key-test-secret",
    SHOW_PUBLIC_IF_NO_TENANT_FOUND=True,
)
class AuthBoundaryTests(TestCase):
    def setUp(self):
        self.platform_user = PlatformUser.objects.create(
            username="platform-admin",
            is_active=True,
            is_platform_admin=True,
        )
        self.api_factory = APIRequestFactory()
        self.tenant = Tenant.objects.create(
            schema_name="client_one",
            name="Client One",
            subdomain="client-one",
        )

        with schema_context(self.tenant.schema_name):
            self.tenant_user = User.objects.create_user(
                username="tenant-admin",
                email="tenant@example.com",
                password="secret123",
                is_staff=True,
            )

    def test_platform_clients_endpoint_accepts_platform_token(self):
        request = self.api_factory.get(
            "/api/platform-mod/clients",
            HTTP_AUTHORIZATION=f"Bearer {generate_token(self.platform_user.id)}",
        )

        response = TenantViewset.as_view({"get": "list"})(request)

        assert response.status_code == 200

    def test_platform_clients_endpoint_rejects_non_platform_token(self):
        token = jwt.encode(
            {
                "user_id": self.platform_user.id,
                "token_type": "tenant_access",
                "exp": datetime.now(UTC) + timedelta(hours=1),
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )

        request = self.api_factory.get(
            "/api/platform-mod/clients",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        response = TenantViewset.as_view({"get": "list"})(request)

        assert response.status_code in {401, 403}

    def test_tenant_user_queryset_reads_from_tenant_schema(self):
        users = _tenant_user_queryset(self.tenant)

        assert any(user.username == self.tenant_user.username for user in users)
