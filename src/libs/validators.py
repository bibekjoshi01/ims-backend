from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError


def validate_positive_integer(value):
    if value <= 0:
        error_message = _("Value must be a positive integer")
        raise ValidationError(error_message)


def validate_alpha(value):
    if not all(char.isalpha() or char.isspace() for char in value):
        error_message = _('"%(value)s" contains non-alphabetic characters') % {
            "value": value,
        }
        raise ValidationError(error_message)


def validate_file_extension(value):
    file_extension_validator = FileExtensionValidator(
        allowed_extensions=["pdf", "doc", "docx", ".png", ".jpg"],
    )
    file_extension_validator(value)


def validate_media_size(value):
    file_size = value.size
    max_size = settings.WEBSITE_MEDIA_MAX_UPLOAD_SIZE

    if file_size > max_size:
        # converting into kb
        f = max_size / 1024
        # converting into MB
        f = f / 1024
        error_message = f"Max size of file is {f} MB"
        raise ValidationError(error_message)
