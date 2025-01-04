import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

# Set up logging
logger = logging.getLogger(__name__)

cipher_suite = Fernet(settings.ENCRYPTION_KEY)


class EncryptedCharField(models.CharField):
    """
    A custom django model field to store encrypted character data.
    """

    def get_prep_value(self, value: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, str):
            # Encode the value and encrypt it
            return cipher_suite.encrypt(value.encode()).decode()
        return value

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            # Decrypt and decode the value
            return cipher_suite.decrypt(value.encode()).decode()

        except InvalidToken as err:
            error_message = f"Decryption failed for value: {value}"
            logger.exception(error_message)
            raise ValueError(error_message) from err

        except Exception as err:
            error_message = (
                f"An unexpected error occurred while decrypting value: {value}"
            )
            logger.exception(error_message)
            raise ValueError(error_message) from err

    def to_python(self, value):
        return self.from_db_value(value, None, None)
