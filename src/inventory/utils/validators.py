import re

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

MAX_PERCENTAGE = 99
EXPECTED_DATE_LENGTH = 10
MAX_MONTH = 12
MAX_DAY = 29


def validate_positive_integer(value):
    if value < 0:
        raise serializers.ValidationError(
            {"error": _("Invalid value! Negative values are not accepted.")},
        )


def validate_percentage(value):
    if value < 0 or value > MAX_PERCENTAGE:
        message = _("Value out of range (0 to 99).")
        raise serializers.ValidationError({"error": message})
    return value


def validate_amount(value):
    if value < 0:
        message = _("Amount should be greater than or equal to 0.")
        raise serializers.ValidationError({"error": message})
    return value


def validate_date_bs(value):
    if len(value.strip()) == EXPECTED_DATE_LENGTH:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            message = _("Invalid date format. The expected format is 'YYYY-MM-DD'.")
            raise serializers.ValidationError(message)

        year, month, day = map(int, value.split("-"))

        if month > MAX_MONTH:
            message = _("Month cannot be greater than 12.")
            raise serializers.ValidationError(message)

        if day > MAX_DAY:
            message = _("Day cannot be greater than 29.")
            raise serializers.ValidationError(message)

    return value
