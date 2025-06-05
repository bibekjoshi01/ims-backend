from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
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
        allowed_extensions=["pdf", "doc", "docx", "png", "jpg", "xlsx"],
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


def validate_unique_fields(
    model,
    attrs,
    fields,
    instance=None,
    field_transform_map=None,  # Optional: normalize like lower/strip
    error_messages=None,
):
    """
    Generic validator for checking uniqueness of one or more fields.

    Args:
        model (models.Model): The model to query.
        attrs (dict): The incoming validated_data or attrs.
        fields (list): List of field names to validate.
        instance (models.Model, optional): Current instance (exclude from check).
        field_transform_map (dict): Optional field transformations.
            Example: {'email': lambda x: x.lower().strip()}
        error_messages (dict): Optional custom error messages per field.
            Example: {'email': 'Email already exists.'}
    """

    field_transform_map = field_transform_map or {}
    error_messages = error_messages or {}

    filters = {}
    for field in fields:
        value = attrs.get(field)
        if value is None:
            continue

        transform = field_transform_map.get(field)
        if transform:
            value = transform(value)
            attrs[field] = value  # set normalized value back to attrs

        filters[field] = value

        # Validate individual field
        if value:
            qs = model.objects.filter(**{field: value}).exclude(is_archived=True)
            if instance:
                qs = qs.exclude(id=instance.id)
            if qs.exists():
                raise serializers.ValidationError(
                    {
                        field: error_messages.get(
                            field,
                            f"{field.capitalize()} must be unique.",
                        ),
                    },
                )

    return attrs
