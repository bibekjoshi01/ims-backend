import logging
from time import perf_counter
from uuid import uuid4

from django.conf import settings
from django.http import JsonResponse

from .request_context import (
    reset_request_context,
    set_request_context,
    set_response_context,
)

access_logger = logging.getLogger("request_access")


class RequestContextMiddleware:
    """
    Attach a request ID and structured request context to every request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _request_id(request):
        incoming_request_id = request.headers.get("X-Request-ID", "").strip()
        if incoming_request_id and len(incoming_request_id) <= 64:
            return incoming_request_id
        return uuid4().hex

    def __call__(self, request):
        schema_name = getattr(getattr(request, "tenant", None), "schema_name", "-")
        request_id = self._request_id(request)
        tokens = set_request_context(
            request_id=request_id,
            schema_name=schema_name,
            method=request.method,
            path=request.path,
        )
        request.request_id = request_id
        started_at = perf_counter()

        try:
            response = self.get_response(request)
        finally:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            set_response_context(status_code="-", duration_ms=duration_ms)
            reset_request_context(tokens)

        response["X-Request-ID"] = request_id
        access_logger.info(
            "request completed",
            extra={
                "request_id": request_id,
                "schema_name": schema_name,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 2),
            },
        )
        return response


class NoIndexMiddleware:
    """
    Attach crawl-prevention headers to production responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not settings.DEBUG:
            response["X-Robots-Tag"] = "noindex, nofollow, noarchive"

        return response


class TenantStatusMiddleware:
    """
    Blocks suspended tenants globally.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(request, "tenant", None)

        if tenant and hasattr(tenant, "is_active"):
            if not tenant.is_active:
                return JsonResponse(
                    {"error": "Your account has been suspended. Please contact software vendor."},
                    status=403,
                )

        return self.get_response(request)


class BlockPostmanMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the 'postman-token' header is present in the request
        if "postman-token" in request.headers:
            return JsonResponse(
                {"error": "Requests from Postman are not allowed"},
                status=403,
            )

        # Continue processing the request if not from Postman
        return self.get_response(request)
