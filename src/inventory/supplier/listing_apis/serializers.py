from rest_framework import serializers
from src.core_app.models import District, TaxGroup


"""Tax Group List Serializer"""


class TaxGroupListSerializerForSupplier(serializers.ModelSerializer):
    class Meta:
        model = TaxGroup
        fields = [
            "id",
            "name",
            "rate",
            "is_default",
        ]


"""Districts List For Supplier"""


class DistrictListSerializerForSupplier(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ["id", "name", "province", "is_default"]
