# Django Imports
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

# Project Imports
from src.base.serializers import AbstractInfoRetrieveSerializer
from src.libs.get_context import get_user_by_context
from .messages import (
    USER_CREATED,
    USER_ERRORS,
    USER_ROLE_CREATED,
    USER_ROLE_ERRORS,
    USER_ROLE_UPDATED,
    USER_UPDATED,
)
from .models import Permission, Role, User
from .utils.generators import generate_role_codename, generate_unique_user_username
from .validators import validate_image


# User Role Serializers


class GetPermissionForRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename", "permission_category"]


class RoleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "codename", "is_active", "created_at"]


class RoleRetrieveSerializer(AbstractInfoRetrieveSerializer):
    permissions = serializers.SerializerMethodField()

    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = Role
        fields = ["id", "name", "codename", "permissions"]

        fields += AbstractInfoRetrieveSerializer.Meta.fields

    def get_permissions(self, obj) -> list:
        permissions = obj.permissions.filter(is_active=True)
        serializer = GetPermissionForRoleSerializer(permissions, many=True)
        return serializer.data


class RoleCreateSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Permission.objects.filter(is_active=True),
        ),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = ["name", "permissions", "is_active"]

    def validate_name(self, name):
        name = name.title()

        if Role.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError(
                USER_ROLE_ERRORS["ROLE_NAME"].format(name=name),
            )
        return name

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        # Get the permissions
        permissions = validated_data.pop("permissions", [])

        # Generate codename
        name = validated_data.get("name")
        codename = generate_role_codename(name)

        # Create Role instance
        role = Role.objects.create(
            name=name.title(),
            codename=codename,
            created_by=created_by,
        )
        role.permissions.set(permissions)
        role.save()
        return role

    def to_representation(self, instance):
        return {"id": instance.id, "message": USER_ROLE_CREATED}


class RolePatchSerializer(serializers.ModelSerializer):
    remarks = serializers.CharField(max_length=50, required=True, write_only=True)
    permissions = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Permission.objects.filter(is_active=True, is_archived=False),
        ),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = ["name", "permissions", "is_active", "remarks"]

    def validate_name(self, name):
        name = name.title()

        if Role.objects.filter(name__iexact=name).exclude(pk=self.instance.id).exists():
            raise serializers.ValidationError(
                USER_ROLE_ERRORS["ROLE_NAME"].format(name=name),
            )
        return name

    def update(self, instance, validated_data):
        name = validated_data.get("name", instance.name)
        # Get the permissions
        permissions = validated_data.get("permissions", [])

        validated_data["codename"] = generate_role_codename(name)

        instance.name = validated_data.get("name", instance.name).title()
        instance.codename = validated_data.get("codename", instance.codename)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.permissions.set(permissions)
        instance.save()

        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": USER_ROLE_UPDATED}


# User Setup Serializers


class GetUserRolesForUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "codename"]


class UserListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username")

    class Meta:
        model = User
        exclude = [
            "uuid",
            "password",
            "is_superuser",
            "is_staff",
            "user_permissions",
            "is_archived",
            "groups",
            "roles",
            "permissions",
        ]


class UserRetrieveSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source="created_by.username")

    class Meta:
        model = User
        exclude = [
            "uuid",
            "password",
            "is_superuser",
            "is_staff",
            "user_permissions",
            "is_archived",
            "groups",
        ]

    def get_roles(self, obj) -> list:
        """
        Return only active, non-archived, and non-system-managed roles.
        """
        roles = obj.roles.filter(is_active=True, is_system_managed=False)
        serializer = GetUserRolesForUserListSerializer(roles, many=True)
        return serializer.data


class UserRegisterSerializer(serializers.ModelSerializer):
    """User Register Serializer"""

    first_name = serializers.CharField(max_length=50, required=True)
    last_name = serializers.CharField(max_length=50, required=True)
    phone_no = serializers.CharField(max_length=15, required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    photo = serializers.ImageField(
        allow_null=True,
        required=False,
        validators=[validate_image],
    )
    roles = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True, is_system_managed=False),
        many=True,
    )
    username = serializers.CharField(allow_blank=True)
    password = serializers.CharField(validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "username",
            "password",
            "email",
            "photo",
            "phone_no",
            "roles",
            "is_active",
        ]

    def validate(self, attrs):
        if attrs["username"]:
            if User.objects.filter(username=attrs["username"]).exists():
                raise serializers.ValidationError(
                    {"username": USER_ERRORS["USERNAME_EXISTS"]},
                )

        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError({"email": USER_ERRORS["EMAIL_EXISTS"]})

        if attrs["phone_no"]:
            if User.objects.filter(phone_no=attrs["phone_no"]).exists():
                raise serializers.ValidationError(
                    {"phone_no": USER_ERRORS["PHONE_EXISTS"]},
                )

        if attrs["roles"] is None or attrs["roles"] == "":
            raise serializers.ValidationError({"roles": USER_ERRORS["MISSING_ROLES"]})

        return attrs

    def create(self, validated_data):
        email = validated_data["email"]
        photo = validated_data.get("photo", None)

        username = validated_data.get("username", "")
        roles = validated_data.pop("roles", [])

        if not username:
            username = generate_unique_user_username(
                user_type="system_user", email=email
            )

        created_by = self.context["request"].user

        user_instance = User.objects.create_system_user(
            first_name=validated_data["first_name"].title(),
            last_name=validated_data["last_name"].title(),
            phone_no=validated_data["phone_no"],
            password=validated_data["password"],
            email=email,
            username=username,
            created_by=created_by,
            context=self.context,
        )

        if photo is not None:
            upload_path = user_instance.get_upload_path(
                upload_path="user/photos",
                filename=photo.name,
            )
            user_instance.photo.save(upload_path, photo)

        user_instance.roles.add(*roles)  # Set the roles

        user_instance.save()

        return user_instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": USER_CREATED}


class UserPatchSerializer(serializers.ModelSerializer):
    """User Update Serializer"""

    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    photo = serializers.ImageField(
        allow_null=True,
        required=False,
        validators=[validate_image],
    )
    phone_no = serializers.CharField(max_length=10, required=False, allow_blank=True)
    roles = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.filter(is_active=True, is_system_managed=False),
        many=True,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "roles",
            "photo",
            "phone_no",
            "is_active",
        ]

    def validate(self, attrs):
        if attrs["phone_no"]:
            if (
                User.objects.filter(phone_no=attrs["phone_no"])
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"phone_no": USER_ERRORS["PHONE_EXISTS"]},
                )

        return attrs

    def update(self, instance: User, validated_data):
        photo = validated_data.get("photo", None)

        instance.first_name = validated_data.get(
            "first_name",
            instance.first_name,
        ).title()
        instance.last_name = validated_data.get("last_name", instance.last_name).title()
        instance.is_active = validated_data.get("is_active", instance.is_active)

        instance.phone_no = validated_data.get("phone_no", instance.phone_no)
        instance.updated_at = timezone.now()

        if "photo" in validated_data:
            if photo is not None:
                upload_path = instance.get_upload_path(
                    upload_path="user/photos",
                    filename=photo.name,
                )
                instance.photo.delete(save=False)  # Remove the old file
                instance.photo.save(upload_path, photo)
            else:
                instance.photo.delete(
                    save=True,
                )  # Delete the existing photo if photo is None

        if "roles" in validated_data:
            system_roles = list(instance.roles.filter(is_system_managed=True))
            roles = validated_data.get("roles", [])
            instance.roles.set(roles)
            instance.roles.add(*system_roles)

        instance.save()
        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": USER_UPDATED}
