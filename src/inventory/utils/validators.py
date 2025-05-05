import re
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


def validate_positive_integer(value):
    if value < 0:
        raise serializers.ValidationError(
            {"error": _("Invalid Value ! Negative Value not accepted.")}
        )


def validate_percentage(value):
    if value < 0 or value > 99:
        raise serializers.ValidationError({"error": _("Value out of range (0 to 99)")})
    return value


def validate_amount(value):
    if value < 0:
        raise serializers.ValidationError(
            {"error": _("Amount should be greater or equal to 0")}
        )
    return value


def validate_date_bs(value):
    if value.strip() == 10:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            raise serializers.ValidationError(
                "Invalid date format. The expected format is 'YYYY-MM-DD'."
            )

        year, month, day = map(int, value.split("-"))

        if month > 12:
            raise serializers.ValidationError("Month cannot be greater than 12.")

        if day > 29:
            raise serializers.ValidationError("Day cannot be greater than 29.")

    return value
