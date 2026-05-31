from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase

from src.libs.middleware import RequestContextMiddleware


class RequestContextMiddlewareTests(SimpleTestCase):
    def setUp(self) -> None:
        self.factory = RequestFactory()

    def test_adds_request_id_header(self) -> None:
        request = self.factory.get("/dashboard")

        response = RequestContextMiddleware(lambda incoming_request: HttpResponse("ok"))(request)

        assert response.status_code == 200
        assert response["X-Request-ID"]
        assert getattr(request, "request_id", None) == response["X-Request-ID"]

    def test_preserves_incoming_request_id(self) -> None:
        request = self.factory.get("/dashboard", HTTP_X_REQUEST_ID="trace-123")

        response = RequestContextMiddleware(lambda incoming_request: HttpResponse("ok"))(request)

        assert response["X-Request-ID"] == "trace-123"
