from uuid import UUID

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class ModelUUIDField(serializers.UUIDField):
    """Custom field to handle UUID input for Model"""

    def to_internal_value(self, data):
        # Convert the incoming UUID to a Model instance
        try:
            uuid_val = UUID(data)  # Validate UUID format
            return self.model.objects.get(
                uuid=uuid_val,
                is_archived=False,
                is_active=True,
            )
        except (ValueError, AttributeError, self.model.DoesNotExist) as err:
            error_message = _("Invalid %s") % self.model.__name__
            raise serializers.ValidationError(error_message) from err


class NotFoundSerializer404(serializers.Serializer):
    """404 Not Found Response"""

    message = serializers.CharField(max_length=255)


class ValidationErrorSerializer400(serializers.Serializer):
    """400 Validation Error Response"""

    error = serializers.CharField(max_length=255)


class SerializerValidationError400(serializers.Serializer):
    """Serializers Field Validation Error Response"""

    error = serializers.ListField(child=serializers.CharField())


class CreatedSuccessfullySerializer201(serializers.Serializer):
    """201 Serializers Created Successfully Response"""

    message = serializers.CharField(max_length=255)


class UnauthorizedSerializer401(serializers.Serializer):
    """401 Unauthorized Response"""

    detail = serializers.CharField(max_length=255)
