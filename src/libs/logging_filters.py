import logging

from .request_context import get_request_context


class RequestContextFilter(logging.Filter):
    def filter(self, record):
        context = get_request_context()
        for key, default in context.items():
            if not hasattr(record, key):
                setattr(record, key, default)
        return True
