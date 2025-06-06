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
from .models import Customer, CustomerAddress


class CustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "full_name",
            "customer_no",
            "gender",
            "is_person",
            "phone_no",
            "alt_phone_no",
            "photo",
            "email",
            "is_active",
        ]


class CustomerAddressListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ["id", "label", "address"]


class CustomerRetrieveSerializer(AbstractInfoRetrieveSerializer):
    addresses = CustomerAddressListSerializer(many=True)

    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = Customer
        custom_fields = [
            "id",
            "full_name",
            "customer_no",
            "is_person",
            "gender",
            "phone_no",
            "alt_phone_no",
            "photo",
            "email",
            "is_active",
            "notes",
            "addresses",
        ]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class CustomerAddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ["label", "address"]


class CustomerCreateSerializer(serializers.ModelSerializer):
    addresses = CustomerAddressCreateSerializer(many=True)

    class Meta:
        model = Customer
        fields = [
            "full_name",
            "is_person",
            "phone_no",
            "alt_phone_no",
            "photo",
            "gender",
            "email",
            "is_active",
            "notes",
            "addresses",
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
        addresses = validated_data.pop("addresses", [])

        created_by = get_user_by_context(self.context)
        customer = Customer.objects.create(
            created_by=created_by,
            **validated_data,
        )

        if addresses:
            for address_data in addresses:
                CustomerAddress.objects.create(
                    customer=customer,
                    created_by=created_by,
                    **address_data,
                )

        return customer

    def to_representation(self, instance):
        return {"id": instance.id, "message": CUSTOMER_CREATE_SUCCESS}


class CustomerAddressUpdateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=CustomerAddress.objects.filter(is_active=True),
    )

    class Meta:
        model = CustomerAddress
        fields = ["id", "label", "address"]


class CustomerPatchSerializer(serializers.ModelSerializer):
    addresses = CustomerAddressUpdateSerializer(many=True)

    class Meta:
        model = Customer
        fields = [
            "full_name",
            "is_person",
            "phone_no",
            "alt_phone_no",
            "gender",
            "photo",
            "email",
            "is_active",
            "notes",
            "addresses",
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
        addresses = validated_data.pop("addresses", [])

        current_user = get_user_by_context(self.context)
        validated_data["updated_by"] = current_user

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save(update_fields=validated_data.keys())

        if addresses:
            for address_data in addresses:
                if "id" in address_data:
                    _id = address_data.pop("id").id
                    address_data["updated_by"] = current_user
                    addresss = instance.addresses.get(id=_id)
                    for attr, value in address_data.items():
                        setattr(addresss, attr, value)

                    addresss.save()
                else:
                    CustomerAddress.objects.create(
                        customer=instance,
                        created_by=current_user,
                        **address_data,
                    )

        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": CUSTOMER_UPDATE_SUCCESS}
