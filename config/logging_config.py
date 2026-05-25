import os
from pathlib import Path

# LOGGING
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR / "src"


# Define the log directory
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

try:
    os.chmod(LOG_DIR, 0o775)
except PermissionError:
    pass


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "src.libs.logging_filters.RequestContextFilter",
        },
    },
    "formatters": {
        "detailed": {
            "format": (
                "[{asctime}] {levelname} {name} "
                "| request_id={request_id} schema={schema_name} "
                "method={method} path={path} status={status_code} duration_ms={duration_ms} "
                "| {filename}:{lineno} in {funcName}() | {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "security_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "security_log"),
            "when": "midnight",  # rotate at midnight
            "interval": 1,  # every 1 day
            "backupCount": 7,  # keep last 7 days
            "formatter": "detailed",
            "level": "INFO",
            "encoding": "utf-8",
            "filters": ["request_context"],
        },
        "server_error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "server_log"),  # base filename
            "when": "midnight",  # rotate at midnight
            "interval": 1,  # every 1 day
            "backupCount": 7,  # keep last 7 days
            "formatter": "detailed",
            "level": "INFO",
            "encoding": "utf-8",
            "filters": ["request_context"],
        },
        "exception_error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "exception_log"),  # base filename
            "when": "midnight",  # rotate at midnight
            "interval": 1,  # every 1 day
            "backupCount": 7,  # keep last 7 days
            "formatter": "detailed",
            "level": "INFO",
            "encoding": "utf-8",
            "filters": ["request_context"],
        },
        "email_error_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "email_log"),  # base filename
            "when": "midnight",  # rotate at midnight
            "interval": 1,  # every 1 day
            "backupCount": 7,  # keep last 7 days
            "formatter": "detailed",
            "level": "INFO",
            "encoding": "utf-8",
            "filters": ["request_context"],
        },
        "access_file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": str(LOG_DIR / "access_log"),
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "formatter": "detailed",
            "level": "INFO",
            "encoding": "utf-8",
            "filters": ["request_context"],
        },
    },
    "loggers": {
        # Django internal logs (Automatic)
        "django.security": {  # CSRF/auth/security warnings
            "handlers": ["security_file"],
            "level": "INFO",
            "propagate": False,
        },
        # Customer Manual logs
        "server_error": {
            "handlers": ["server_error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "exception_error": {
            "handlers": ["exception_error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "email_error": {
            "handlers": ["email_error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "request_access": {
            "handlers": ["access_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
