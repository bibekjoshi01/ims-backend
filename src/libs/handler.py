import logging
import traceback

from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler

logger = logging.getLogger("exception_error")


def custom_exception_handler(exc, context):
    # Log the error if it's not a validation error
    if isinstance(exc, ValidationError):
        tb = traceback.format_tb(exc.__traceback__)
        error_msg = f"ValidationError occurred: {exc} \n{''.join(tb)}"
        logger.error(error_msg)

    return exception_handler(exc, context=context)
