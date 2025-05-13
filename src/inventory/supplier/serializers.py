from rest_framework import serializers
from django.contrib.auth import get_user_model

from src.base.serializers import AbstractInfoRetrieveSerializer
from src.libs.get_context import get_user_by_context
from .messages import (
    SUPPLIER_CREATE_SUCCESS,
    SUPPLIER_EMAIL_ALREADY_EXISTS,
    SUPPLIER_UPDATE_SUCCESS,
)
from src.user.utils.generators import (
    generate_strong_password,
    generate_unique_user_username,
)
from .models import InvSupplier

User = get_user_model()


class UserDetailListSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "phone_no", "email", "username"]


class UserDetailCreateUpdateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="first_name", required=True)

    class Meta:
        model = User
        fields = ["full_name", "email", "photo", "phone_no"]


class InvSupplierListSerializer(serializers.ModelSerializer):
    details = UserDetailListSerializer(source="user")

    class Meta:
        model = InvSupplier
        fields = ["id", "opening_balance", "remarks", "details", "is_active"]


class InvSupplierRetrieveSerializer(AbstractInfoRetrieveSerializer):
    details = UserDetailListSerializer(source="user")

    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = InvSupplier
        custom_fields = ["id", "opening_balance", "remarks", "details"]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class InvSupplierCreateSerializer(serializers.ModelSerializer):
    details = UserDetailCreateUpdateSerializer()

    class Meta:
        model = InvSupplier
        fields = ["opening_balance", "remarks", "details", "is_active"]

    def validate_user_details(self, user_details):
        email = user_details.get("email", "")

        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": SUPPLIER_EMAIL_ALREADY_EXISTS})

        return user_details

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        user_details = validated_data.pop("details", {})
        username = generate_unique_user_username(type="supplier")

        # User Instance Creation
        user_instance = User.objects.create_inventory_supplier(
            username=username,
            first_name=user_details.get("full_name", ""),
            email=user_details.get("email", ""),
            photo=user_details.get("photo", ""),
            phone_no=user_details.get("phone_no", ""),
            password=generate_strong_password(),
            created_by=created_by,
        )

        suppliler = InvSupplier.objects.create(
            user=user_instance,
            opening_balance=validated_data.get("opening_balance", 0.0),
            remarks=validated_data.get("remarks", ""),
            is_active=validated_data.get("is_active", True),
            created_by=created_by,
        )

        return suppliler

    def to_representation(self, instance):
        return {"id": instance.id, "message": SUPPLIER_CREATE_SUCCESS}


class InvSupplierPatchSerializer(serializers.ModelSerializer):
    details = UserDetailCreateUpdateSerializer()

    class Meta:
        model = InvSupplier
        fields = ["opening_balance", "remarks", "details", "is_active"]

    def update(self, instance, validated_data):
        user_details_data = validated_data.pop("details", {})

        if user_details_data:
            user_instance = instance.user

            email = user_details_data.get("email", "")

            # Check if the email is being updated and it already exists for another user
            if (
                email
                and User.objects.exclude(id=user_instance.id)
                .filter(email=email)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"email": SUPPLIER_EMAIL_ALREADY_EXISTS}
                )

            user_instance.first_name = user_details_data.get(
                "full_name", user_instance.first_name
            )
            user_instance.email = user_details_data.get("email", user_instance.email)
            user_instance.photo = user_details_data.get("photo", user_instance.photo)
            user_instance.phone_no = user_details_data.get(
                "phone_no", user_instance.phone_no
            )
            user_instance.save()

        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.opening_balance = validated_data.get(
            "opening_balance", instance.opening_balance
        )
        instance.remarks = validated_data.get("remarks", instance.remarks)
        instance.save()

        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": SUPPLIER_UPDATE_SUCCESS}
