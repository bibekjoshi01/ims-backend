import logging
import traceback

from django.http import HttpRequest
from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

from .request_context import get_request_context

logger = logging.getLogger("exception_error")


def custom_exception_handler(exc, context):
    request: HttpRequest | None = context.get("request")
    request_context = get_request_context()
    log_extra = {
        "request_id": request_context["request_id"],
        "schema_name": request_context["schema_name"],
        "method": request_context["method"],
        "path": request_context["path"],
        "status_code": "-",
        "duration_ms": "-",
    }

    if request is not None:
        log_extra["method"] = request.method
        log_extra["path"] = request.path
        log_extra["schema_name"] = getattr(getattr(request, "tenant", None), "schema_name", "-")
        log_extra["request_id"] = getattr(request, "request_id", request_context["request_id"])

    tb = "".join(traceback.format_tb(exc.__traceback__))
    if isinstance(exc, ValidationError):
        logger.warning(
            "validation error",
            extra={
                **log_extra,
                "detail": str(exc),
                "traceback": tb,
            },
        )
    else:
        logger.error(
            "api exception",
            extra={
                **log_extra,
                "detail": str(exc),
                "traceback": tb,
            },
        )

    return exception_handler(exc, context=context)
