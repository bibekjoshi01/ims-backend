from rest_framework import serializers

from src.purchase.models import (
    PurchaseAdditionalCharge,
    PurchaseAttachment,
    PurchaseDetailSerialNumber,
)


class PurchaseAdditionalChargeTypeListSerializer(serializers.ModelSerializer): ...
