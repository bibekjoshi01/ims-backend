from rest_framework import serializers

# Project Imports
from src.base.serializers import AbstractInfoRetrieveSerializer
from src.libs.get_context import get_user_by_context
from src.libs.validators import validate_unique_fields

from .messages import (
    SUPPLIER_CREATE_SUCCESS,
    SUPPLIER_EMAIL_ALREADY_EXISTS,
    SUPPLIER_PHONE_ALREADY_EXISTS,
    SUPPLIER_UPDATE_SUCCESS,
    SUPPLIER_WEBSITE_ALREADY_EXISTS,
)
from .models import Supplier


class SupplierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "contact_person",
            "email",
            "phone_no",
            "alt_phone_no",
            "address",
            "country",
            "website",
            "tax_id",
            "is_active",
        ]


class SupplierRetrieveSerializer(AbstractInfoRetrieveSerializer):
    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = Supplier
        custom_fields = [
            "id",
            "name",
            "contact_person",
            "email",
            "phone_no",
            "alt_phone_no",
            "address",
            "country",
            "website",
            "tax_id",
            "notes",
        ]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class SupplierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "name",
            "contact_person",
            "email",
            "phone_no",
            "alt_phone_no",
            "address",
            "country",
            "website",
            "tax_id",
            "notes",
            "is_active",
        ]

    def validate(self, attrs):
        return validate_unique_fields(
            model=Supplier,
            attrs=attrs,
            fields=["name", "email", "phone_no", "alt_phone_no", "website"],
            field_transform_map={
                "name": lambda x: x.strip(),
                "email": lambda x: x.lower().strip(),
                "phone_no": lambda x: x.strip(),
                "alt_phone_no": lambda x: x.strip(),
                "website": lambda x: x.lower().strip(),
            },
            error_messages={
                "email": SUPPLIER_EMAIL_ALREADY_EXISTS,
                "phone_no": SUPPLIER_PHONE_ALREADY_EXISTS,
                "alt_phone_no": SUPPLIER_PHONE_ALREADY_EXISTS,
                "website": SUPPLIER_WEBSITE_ALREADY_EXISTS,
            },
        )

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        return Supplier.objects.create(
            created_by=created_by,
            **validated_data,
        )

    def to_representation(self, instance):
        return {"id": instance.id, "message": SUPPLIER_CREATE_SUCCESS}


class SupplierPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "name",
            "contact_person",
            "email",
            "phone_no",
            "alt_phone_no",
            "address",
            "country",
            "website",
            "tax_id",
            "notes",
            "is_active",
        ]

    def validate(self, attrs):
        return validate_unique_fields(
            model=Supplier,
            attrs=attrs,
            fields=["name", "email", "phone_no", "alt_phone_no", "website"],
            instance=self.instance,
            field_transform_map={
                "name": lambda x: x.strip(),
                "email": lambda x: x.lower().strip(),
                "phone_no": lambda x: x.strip(),
                "alt_phone_no": lambda x: x.strip(),
                "website": lambda x: x.lower().strip(),
            },
            error_messages={
                "email": SUPPLIER_EMAIL_ALREADY_EXISTS,
                "phone_no": SUPPLIER_PHONE_ALREADY_EXISTS,
                "alt_phone_no": SUPPLIER_PHONE_ALREADY_EXISTS,
                "website": SUPPLIER_WEBSITE_ALREADY_EXISTS,
            },
        )

    def update(self, instance, validated_data):
        validated_data["updated_by"] = get_user_by_context(self.context)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save(update_fields=validated_data.keys())
        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": SUPPLIER_UPDATE_SUCCESS}
