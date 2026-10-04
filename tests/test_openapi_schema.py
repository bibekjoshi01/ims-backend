"""The API contract must show authentication on protected tenant endpoints."""

from django.test import SimpleTestCase
from drf_spectacular.generators import SchemaGenerator


class TenantOpenAPITests(SimpleTestCase):
    def test_tenant_endpoints_document_bearer_authentication(self):
        schema = SchemaGenerator(urlconf="config.tenant_urls").get_schema(public=True)
        scheme = schema["components"]["securitySchemes"]["TenantJWTAuth"]
        assert scheme == {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
        paths = schema["paths"]
        for path in (
            "/api/v1/internal/user-mod/users",
            "/api/v1/internal/performance-mod/analytics/overview",
            "/api/v1/internal/students-mod/students",
            "/api/v1/internal/performance-mod/student-portal/overview",
            "/api/v1/internal/performance-mod/student-portal/subjects/{enrollment_id}",
            "/api/v1/internal/performance-mod/student-portal/subjects/{enrollment_id}/attendance",
        ):
            assert {"TenantJWTAuth": []} in paths[path]["get"]["security"]
            assert {} not in paths[path]["get"]["security"]
        assert {} in paths["/api/v1/internal/user-mod/account/login"]["post"]["security"]

    def test_student_contract_has_no_staff_aggregates_or_write_operations(self):
        schema = SchemaGenerator(urlconf="config.tenant_urls").get_schema(public=True)
        schemas = schema["components"]["schemas"]
        assert "studentCount" not in schemas["PortalClass"]["properties"]
        assert "attendancePercentage" not in schemas["PortalClass"]["properties"]
        assert set(schemas["PortalTeacher"]["properties"]) == {"fullName"}
        assert "class" in schemas["PortalSubject"]["properties"]
        for path, operations in schema["paths"].items():
            if "/performance-mod/student-portal/" in path:
                assert set(operations) == {"get"}
