from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from src.base.serializers import AbstractInfoRetrieveSerializer
from src.libs.get_context import get_user_by_context
from src.user.utils.generate_password import generate_strong_password
from src.user.utils.verification import send_user_forget_password_email
from src.user.validators import validate_image

from .models import (
    User,
    UserAccountVerification,
    UserForgetPasswordRequest,
    UserGroup,
    UserPermission,
)
from .utils.generate_codename import generate_user_group_codename
from .utils.generate_username import generate_unique_user_username

# User Group Serializers


class GetUserPermissionForUserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPermission
        fields = ["id", "name", "codename", "permission_category"]


class UserGroupListSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserGroup
        fields = ["id", "name", "codename", "is_active"]


class UserGroupRetrieveSerializer(AbstractInfoRetrieveSerializer):
    permissions = GetUserPermissionForUserGroupSerializer(many=True)

    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = UserGroup
        fields = [
            "id",
            "name",
            "codename",
            "permissions",
        ]

        fields += AbstractInfoRetrieveSerializer.Meta.fields


class UserGroupCreateSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=UserPermission.objects.filter(is_active=True, is_archived=False),
        ),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = UserGroup
        fields = ["name", "permissions"]

    def validate_name(self, name):
        name = name.title()

        if UserGroup.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError(
                {"error": f"User group with name {name} already exists."},
            )
        return name

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)

        permissions = validated_data.pop("permissions", None)
        name = validated_data.get("name")

        # Generate codename directly without modifying validated_data
        codename = generate_user_group_codename(name)

        # Create UserGroup instance with created_by and codename
        user_group_instance = UserGroup.objects.create(
            **validated_data,
            created_by=created_by,
            codename=codename,
        )

        # Add permissions if provided
        if permissions:
            user_group_instance.permissions.set(list(permissions))

        return user_group_instance

    def to_representation(self, instance):
        return {"message": "User Group Created Successfully."}


class UserGroupPatchSerializer(serializers.ModelSerializer):
    remarks = serializers.CharField(max_length=50, required=True, write_only=True)
    permissions = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=UserPermission.objects.filter(is_active=True, is_archived=False),
        ),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = UserGroup
        fields = ["name", "permissions", "is_active", "remarks"]

    def validate(self, attrs):
        name = attrs["name"].title()

        if (
            UserGroup.objects.filter(name__iexact=name)
            .exclude(pk=self.instance.id)
            .exists()
        ):
            raise serializers.ValidationError(
                {"name": f"User group with name {name} already exists."},
            )

        return name

    def update(self, instance, validated_data):
        permissions = validated_data.pop(
            "permissions",
            instance.permissions.values_list("id", flat=True),
        )
        name = validated_data.get("name", instance.name)
        validated_data["codename"] = generate_user_group_codename(name)

        instance.name = name
        instance.codename = validated_data.get("codename", instance.codename)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.permissions.set(list(permissions))
        instance.save()

        return validated_data

    def to_representation(self, instance):
        return {"message": "User Group Updated Successfully."}


# User Setup Serializers


class GetUserGroupsForUserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = [
            "id",
            "name",
        ]

    def get_queryset(self):
        """
        Filter queryset to include only active user groups.
        """
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)


class UserListSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username")

    class Meta:
        model = User
        exclude = [
            "password",
            "is_superuser",
            "is_staff",
            "user_permissions",
            "groups",
        ]


class UserRetrieveSerializer(serializers.ModelSerializer):
    groups = GetUserGroupsForUserListSerializer(many=True)
    created_by_username = serializers.CharField(source="created_by.username")

    class Meta:
        model = User
        exclude = ["password", "is_superuser", "is_staff"]


class UserRegisterSerializer(serializers.ModelSerializer):
    """User Register Serializer"""

    first_name = serializers.CharField(max_length=50, required=True)
    middle_name = serializers.CharField(max_length=50, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=True)
    phone_no = serializers.CharField(max_length=15, required=False)
    email = serializers.EmailField(required=True)
    photo = serializers.ImageField(
        allow_null=True,
        required=False,
        validators=[validate_image],
    )
    groups = serializers.PrimaryKeyRelatedField(
        queryset=UserGroup.objects.exclude(is_system_managed=True),
        many=True,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "photo",
            "phone_no",
            "groups",
        ]

    def validate(self, attrs):
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": "User already exists with this email."},
            )

        if attrs["groups"] is None or attrs["groups"] == "":
            raise serializers.ValidationError({"groups": "Please provide user group."})

        return attrs

    def create(self, validated_data):
        email = validated_data["email"]
        photo = validated_data.get("photo", None)

        username = generate_unique_user_username(user_type="system_user")
        password = generate_strong_password()

        created_by = self.context["request"].user

        user_instance = User.objects.create_system_user(
            first_name=validated_data["first_name"].title(),
            middle_name=validated_data.get("middle_name", "").title(),
            last_name=validated_data["last_name"].title(),
            phone_no=validated_data["phone_no"],
            password=password,
            email=email,
            username=username,
            created_by=created_by,
        )

        if photo is not None:
            upload_path = user_instance.get_upload_path(
                upload_path="user/photos",
                filename=photo.name,
            )
            user_instance.photo.save(upload_path, photo)

        for group in validated_data["groups"]:
            user_instance.groups.add(group)

        user_instance.save()

        return user_instance

    def to_representation(self, instance):
        return {"message": "User Registered Successfully."}


class UserPatchSerializer(serializers.ModelSerializer):
    """User Update Serializer"""

    first_name = serializers.CharField(max_length=50, required=False)
    middle_name = serializers.CharField(max_length=50, allow_blank=True, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    photo = serializers.ImageField(
        allow_null=True,
        required=False,
        validators=[validate_image],
    )
    phone_no = serializers.CharField(max_length=10, required=False)
    groups = serializers.PrimaryKeyRelatedField(
        queryset=UserGroup.objects.exclude(is_system_managed=True),
        many=True,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "groups",
            "photo",
            "phone_no",
        ]

    def update(self, instance, validated_data):
        photo = validated_data.pop("photo", None)
        user = instance

        user.first_name = validated_data.get("first_name", "").title()
        user.middle_name = validated_data.get("middle_name", "").title()
        user.last_name = validated_data.get("last_name", "").title()

        user.phone_no = validated_data.get("phone_no", user.phone_no)
        user.updated_at = timezone.now()

        if photo:
            upload_path = instance.get_upload_path(
                upload_path="user/photos",
                filename=photo.name,
            )
            instance.photo.delete(save=False)  # Remove the old file
            instance.photo.save(upload_path, photo)

        # remove existing groups
        for group in instance.groups.exclude(codename="SYSTEM-USER"):
            instance.groups.remove(group)

        # add new groups
        for group in validated_data.get("groups", []):
            instance.groups.add(group)

        user.save()
        return user

    def to_representation(self, instance):
        return {"message": "User Updated Successfully."}


# User Serializers


class GetUserPermissionsSerializer(serializers.ModelSerializer):
    main_module = serializers.ReadOnlyField(source="permission_category.main_module.id")
    main_module_name = serializers.ReadOnlyField(
        source="permission_category.main_module.name",
    )
    permission_category_name = serializers.ReadOnlyField(
        source="permission_category.name",
    )

    class Meta:
        model = UserPermission
        fields = [
            "id",
            "name",
            "codename",
            "permission_category",
            "permission_category_name",
            "main_module",
            "main_module_name",
        ]


class GetGroupAndPermissionForLoginSerializer(serializers.ModelSerializer):
    permissions = GetUserPermissionsSerializer(many=True, allow_null=True)

    class Meta:
        model = UserGroup
        exclude = ["created_at", "created_by"]


class UserLoginSerializer(serializers.ModelSerializer):
    """User Login Serializer"""

    persona = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ["password", "persona"]

    def validate(self, attrs):
        persona = attrs.get("persona", None)
        password = attrs.pop("password", "")

        try:
            if "@" in persona:
                user = User.objects.get(email=persona)
            else:
                user = User.objects.get(username=persona)
        except User.DoesNotExist as err:
            raise serializers.ValidationError(
                {"persona": "Invalid credentials, Try again!"},
            ) from err

        if not user.check_password(password):
            raise serializers.ValidationError(
                {"password": "Invalid password, try again!"},
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {"persona": "Account disabled, contact admin!"},
            )

        context = {"request": self.context.get("request")}
        groups = user.groups.filter(is_archived=False, is_active=True)
        user_permissions = user.user_permissions.filter(
            is_archived=False,
            is_active=True,
        )
        group_serializer = GetGroupAndPermissionForLoginSerializer(
            groups,
            many=True,
            context=context,
        )
        user_permissions_serializer = GetUserPermissionsSerializer(
            user_permissions,
            many=True,
            context=context,
        )

        # Update the last login datetime
        user.last_login = timezone.now()
        user.save()

        return {
            "message": "Logged In Successfully.",
            "id": user.id,
            "is_superuser": user.is_superuser,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "phone_no": user.phone_no,
            "email": user.email,
            "tokens": user.tokens,
            "groups": group_serializer.data,
            "user_permissions": user_permissions_serializer.data,
        }


class UserLogoutSerializer(serializers.Serializer):
    """User Logout Serializer"""

    refresh = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={"required": "Refresh token is required."},
    )

    def validate(self, attrs):
        refresh_token = attrs.get("refresh", None)
        try:
            RefreshToken(refresh_token)
        except Exception as err:
            raise serializers.ValidationError(
                {"refresh": "Invalid Refresh Token"},
            ) from err

        return attrs

    def create(self, validated_data):
        refresh_token = validated_data.get("refresh", None)
        try:
            RefreshToken(refresh_token).blacklist()
        except Exception as err:
            error_message = "Invalid Refresh Token"
            raise serializers.ValidationError(error_message) from err
        return validated_data


class UserProfileSerializer(serializers.ModelSerializer):
    """User Profile Serializer"""

    full_name = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "photo",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "full_name",
            "phone_no",
            "email",
            "is_superuser",
            "date_joined",
            "is_active",
            "is_email_verified",
            "is_phone_verified",
            "groups",
        ]

    def get_full_name(self, obj) -> str:
        return obj.get_full_name

    def get_groups(self, obj) -> list:
        return list(obj.groups.values_list("name", flat=True))


class UserChangePasswordSerializer(serializers.Serializer):
    """User Change Password Serializer"""

    old_password = serializers.CharField(max_length=128, required=True)
    new_password = serializers.CharField(max_length=128, required=True)
    confirm_password = serializers.CharField(max_length=128, required=True)

    def validate(self, attrs):
        user = get_user_by_context(self.context)
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        # Check if old password matches
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"old_password": "Incorrect old password."},
            )

        # Check if new password and old password are same
        if new_password == old_password:
            raise serializers.ValidationError(
                {"new_password": "New password must be different from old password."},
            )

        # Check if new password and confirm password match
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "New password and confirm password do not match."},
            )

        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """User Profile Update Serializer"""

    first_name = serializers.CharField(max_length=50, required=False)
    middle_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False)
    phone_no = serializers.CharField(max_length=10, required=False)
    photo = serializers.ImageField(
        allow_null=True, required=False, validators=[validate_image],
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "photo",
            "phone_no",
        ]

    def update(self, instance, validated_data):
        photo = validated_data.pop("photo", None)
        user = instance
        user.first_name = validated_data.get("first_name", "").strip().title()
        user.middle_name = validated_data.get("middle_name", "").strip().title()
        user.last_name = validated_data.get("last_name", "").strip().title()

        user.phone_no = validated_data.get("phone_no", user.phone_no)
        user.updated_at = timezone.now()

        if photo:
            upload_path = instance.get_upload_path(
                upload_path="user/photos",
                filename=photo.name,
            )
            instance.photo.delete(save=False)  # Remove the old file
            instance.photo.save(upload_path, photo)

        user.save()

        return user


class UserForgetPasswordRequestSerializer(serializers.Serializer):
    """User Forget Password Request Serializer"""

    email = serializers.EmailField(required=True)

    def validate(self, attrs):
        email = attrs.get("email", "")
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                raise serializers.ValidationError(
                    {"email": "Account Disabled, Contact admin!"},
                )
            attrs["user"] = user
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": f"Account with email {email} do not exists."},
            ) from None

        return attrs

    def create(self, validated_data):
        user = validated_data.pop("user", None)
        if user is not None:
            # Filter forget password requests by user and is_archived flag
            forget_password_requests = UserForgetPasswordRequest.objects.filter(
                user=user,
                is_archived=False,
            )
            # Archive the filtered requests
            forget_password_requests.update(is_archived=True)
            # Send the email
            send_user_forget_password_email(
                recipient_email=validated_data["email"],
                user_id=user.id,
                request=self.context["request"],
            )

        return validated_data


class UserForgetPasswordSerializer(serializers.Serializer):
    """User Forget Password Serializer"""

    token = serializers.CharField(max_length=64, required=True)
    new_password = serializers.CharField(max_length=32, required=True)
    confirm_password = serializers.CharField(max_length=32, required=True)

    def validate(self, attrs):
        token = attrs.get("token")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        try:
            forget_password_request = UserForgetPasswordRequest.objects.get(
                token=token,
                is_archived=False,
            )
            now = timezone.now()
            delta = now - forget_password_request.created_at
            if delta > timedelta(minutes=settings.AUTH_LINK_EXP_TIME):
                forget_password_request.is_archived = True
                forget_password_request.save()
                raise serializers.ValidationError(
                    {"token": "Link has Expired, Try Again!"},
                )
        except UserForgetPasswordRequest.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid Link."}) from None

        user = forget_password_request.user
        old_password = user.password
        attrs["forget_password_request"] = forget_password_request

        # Check if new password and old password are same
        if check_password(new_password, old_password):
            raise serializers.ValidationError(
                {"new_password": "New password must be different from old password."},
            )

        # Check if new password and confirm password match
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "New password and confirm password do not match."},
            )

        return attrs

    def create(self, validated_data):
        new_password = validated_data["new_password"]
        forget_password_request = validated_data.get("forget_password_request")

        user = forget_password_request.user
        user.set_password(new_password)
        user.save()
        forget_password_request.is_archived = True
        forget_password_request.save()

        return validated_data


class UserVerifyAccountSerializer(serializers.Serializer):
    """User Verify Account Serializer"""

    token = serializers.CharField(max_length=256, required=True)

    def validate(self, attrs):
        token = attrs.get("token")

        try:
            verification_request = UserAccountVerification.objects.get(
                token=token,
                is_archived=False,
            )
            now = timezone.now()
            delta = now - verification_request.created_at

            if verification_request.user.is_email_verified:
                verification_request.is_archived = True
                verification_request.save()
                raise serializers.ValidationError(
                    {"email": "Email already verified. Try LogIn !"},
                )

            if delta > timedelta(minutes=settings.AUTH_LINK_EXP_TIME):
                verification_request.is_archived = True
                verification_request.save()
                raise serializers.ValidationError(
                    {"token": "Link has Expired, Try Again!"},
                )

        except UserAccountVerification.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid Link."}) from None

        attrs["verification_request"] = verification_request

        return attrs

    def create(self, validated_data):
        verification_request = validated_data["verification_request"]
        user_instance = verification_request.user
        user_instance.is_email_verified = True
        user_instance.save()
        verification_request.is_archived = True
        verification_request.save()
        return validated_data
