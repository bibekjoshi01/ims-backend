import logging
from typing import ClassVar

from .request_context import get_request_context


class RequestContextFilter(logging.Filter):
    DEFAULTS: ClassVar[dict[str, str]] = {
        "request_id": "-",
        "schema_name": "-",
        "method": "-",
        "path": "-",
        "status_code": "-",
        "duration_ms": "-",
        "user_id": "-",
        "ip_address": "-",
    }

    def filter(self, record):
        context = get_request_context() or {}

        for key, default in self.DEFAULTS.items():
            value = context.get(key)
            setattr(record, key, default if value is None else value)

        return True
