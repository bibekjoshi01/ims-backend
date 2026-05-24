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
    "formatters": {
        "detailed": {
            "format": (
                "[{asctime}] {levelname} "
                "{name} | {filename}:{lineno} in {funcName}() | {message}"
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
    },
}
