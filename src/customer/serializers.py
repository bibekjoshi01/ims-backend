from rest_framework import serializers

# Project Imports
from src.base.serializers import AbstractInfoRetrieveSerializer
from src.libs.get_context import get_user_by_context
from src.libs.validators import validate_unique_fields

from .messages import (
    CUSTOMER_CREATE_SUCCESS,
    CUSTOMER_EMAIL_ALREADY_EXISTS,
    CUSTOMER_PHONE_ALREADY_EXISTS,
    CUSTOMER_UPDATE_SUCCESS,
)
from .models import Customer


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "full_name",
            "customer_no",
            "is_person",
            "phone_no",
            "alt_phone_no",
            "photo",
            "email",
            "is_active",
        ]


class CustomerRetrieveSerializer(AbstractInfoRetrieveSerializer):
    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = Customer
        custom_fields = [
            "id",
            "full_name",
            "customer_no",
            "is_person",
            "phone_no",
            "alt_phone_no",
            "photo",
            "email",
            "is_active",
            "notes",
        ]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class CustomerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "full_name",
            "is_person",
            "phone_no",
            "alt_phone_no",
            "photo",
            "email",
            "is_active",
            "notes",
        ]

    def validate(self, attrs):
        return validate_unique_fields(
            model=Customer,
            attrs=attrs,
            fields=["email", "phone_no", "alt_phone_no"],
            field_transform_map={
                "email": lambda x: x.lower().strip(),
                "phone_no": lambda x: x.strip(),
                "alt_phone_no": lambda x: x.strip(),
            },
            error_messages={
                "email": CUSTOMER_EMAIL_ALREADY_EXISTS,
                "phone_no": CUSTOMER_PHONE_ALREADY_EXISTS,
                "alt_phone_no": CUSTOMER_PHONE_ALREADY_EXISTS,
            },
        )

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        return Customer.objects.create(
            created_by=created_by,
            **validated_data,
        )

    def to_representation(self, instance):
        return {"id": instance.id, "message": CUSTOMER_CREATE_SUCCESS}


class CustomerPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "full_name",
            "is_person",
            "phone_no",
            "alt_phone_no",
            "photo",
            "email",
            "is_active",
            "notes",
        ]

    def validate(self, attrs):
        return validate_unique_fields(
            model=Customer,
            attrs=attrs,
            fields=["email", "phone_no", "alt_phone_no"],
            instance=self.instance,
            field_transform_map={
                "email": lambda x: x.lower().strip(),
                "phone_no": lambda x: x.strip(),
                "alt_phone_no": lambda x: x.strip(),
            },
            error_messages={
                "email": CUSTOMER_EMAIL_ALREADY_EXISTS,
                "phone_no": CUSTOMER_PHONE_ALREADY_EXISTS,
                "alt_phone_no": CUSTOMER_PHONE_ALREADY_EXISTS,
            },
        )

    def update(self, instance, validated_data):
        validated_data["updated_by"] = get_user_by_context(self.context)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save(update_fields=validated_data.keys())
        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": CUSTOMER_UPDATE_SUCCESS}
