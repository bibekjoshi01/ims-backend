from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from tenants.models import Domain, Tenant
from tenants.validators import RESERVED_SUBDOMAINS, subdomain_validator

User = get_user_model()


class TenantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "subdomain",
            "is_active",
            "created_at",
            "activated_at",
            "suspended_at",
        ]


class TenantRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "subdomain",
            "is_active",
            "created_at",
            "activated_at",
            "suspended_at",
        ]


class TenantCreateSerializer(serializers.ModelSerializer):
    subdomain = serializers.CharField(
        min_length=3,
        max_length=63,
        validators=[subdomain_validator],
    )

    def validate_subdomain(self, value):
        value = value.strip().lower()

        if value in RESERVED_SUBDOMAINS:
            raise serializers.ValidationError("This subdomain is reserved.")

        return value

    class Meta:
        model = Tenant
        fields = ["id", "name", "subdomain", "is_active"]

    def create(self, validated_data):
        subdomain = validated_data["subdomain"]

        tenant = Tenant.objects.create(
            **validated_data,
            schema_name=subdomain,
        )

        Domain.objects.create(
            tenant=tenant,
            domain=f"{subdomain}{settings.ALLOWED_HOSTS[0]}",
            is_primary=True,
        )

        if tenant.is_active:
            tenant.activate()
        else:
            tenant.suspend()

        return tenant


class TenantPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "subdomain", "is_active"]

    def update(self, instance, validated_data):
        new_subdomain = validated_data.get("subdomain")

        if new_subdomain and new_subdomain != instance.subdomain:
            domain = instance.domains.get(is_primary=True)
            domain.domain = f"{new_subdomain}{settings.ALLOWED_HOSTS[0]}"
            domain.save()

            instance.subdomain = new_subdomain

        instance.name = validated_data.get("name", instance.name)
        if "is_active" in validated_data:
            instance.is_active = validated_data["is_active"]

        instance.save()

        if "is_active" in validated_data:
            if instance.is_active:
                instance.activate()
            else:
                instance.suspend()

        return instance


class TenantUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_no",
            "is_staff",
            "is_superuser",
            "is_active",
        ]


class TenantUserRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_no",
            "is_staff",
            "is_superuser",
            "is_active",
        ]


class TenantUserCreateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    is_superuser = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_no",
            "is_staff",
            "is_superuser",
            "password",
            "is_active",
        ]

    def validate_username(self, value):
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data["is_staff"] = validated_data.get("is_staff", True) or validated_data.get(
            "is_superuser", False
        )
        user = User.objects.create(**validated_data)
        user.set_password(password)

        user.save()
        return user


class TenantUserPatchSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "phone_no",
            "is_staff",
            "password",
            "is_superuser",
            "is_active",
        ]

    def validate_username(self, value):
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        # update normal fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if instance.is_superuser:
            instance.is_staff = True

        # handle password separately
        if password:
            instance.set_password(password)

        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
