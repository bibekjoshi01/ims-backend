import logging

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from .request_context import get_request_context

exception_logger = logging.getLogger("exception_error")
validation_logger = logging.getLogger("validation_error")


def custom_exception_handler(exc, context):
    ctx = get_request_context() or {}

    # Validation errors (expected)
    # -------------------------
    if isinstance(exc, ValidationError):
        validation_logger.warning(
            "validation error",
            extra={
                "request_id": ctx.get("request_id", "-"),
                "schema_name": ctx.get("schema_name", "-"),
                "method": ctx.get("method", "-"),
                "path": ctx.get("path", "-"),
                "status_code": 400,
                "duration_ms": ctx.get("duration_ms", "-"),
                "detail": getattr(exc, "detail", str(exc)),
            },
        )

    # System errors (unexpected)
    # -------------------------
    else:
        exception_logger.exception(
            "api exception",
            extra={
                "request_id": ctx.get("request_id", "-"),
                "schema_name": ctx.get("schema_name", "-"),
                "method": ctx.get("method", "-"),
                "path": ctx.get("path", "-"),
            },
        )

    response = exception_handler(exc, context)

    if response is not None and isinstance(response.data, dict):
        response.data.setdefault("success", False)

    return response
