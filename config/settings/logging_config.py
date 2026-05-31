import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _as_bool(value):
    return value.strip().lower() in {"1", "true", "yes", "on"}


BASE_DIR = Path(__file__).resolve().parent.parent.parent

DEBUG = _as_bool(os.getenv("DEBUG", "True"))

LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "src.libs.logging_filters.RequestContextFilter",
        },
    },
    "formatters": {
        # Dev readable format
        "pretty": {
            "format": (
                "[{asctime}] {levelname} {name} "
                "| request_id={request_id} "
                "| schema={schema_name} "
                "| method={method} "
                "| path={path} "
                "| status={status_code} "
                "| duration={duration_ms}ms "
                "| {message}"
            ),
            "style": "{",
        },
        # Prod JSON format
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": (
                "%(asctime)s "
                "%(levelname)s "
                "%(name)s "
                "%(request_id)s "
                "%(schema_name)s "
                "%(method)s "
                "%(path)s "
                "%(status_code)s "
                "%(duration_ms)s "
                "%(message)s"
            ),
        },
    },
    "handlers": {
        # DEV: file logging (human readable)
        "dev_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "when": "midnight",
            "backupCount": 7,
            "formatter": "pretty",
            "filters": ["request_context"],
        },
        # PROD: stdout JSON
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_context"],
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.utils.autoreload": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "request_access": {
            "handlers": ["dev_file" if DEBUG else "console"],
            "level": "INFO",
            "propagate": False,
        },
        "exception_error": {
            "handlers": ["dev_file" if DEBUG else "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "validation_error": {
            "handlers": ["dev_file" if DEBUG else "console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["dev_file" if DEBUG else "console"],
        "level": LOG_LEVEL,
    },
}
