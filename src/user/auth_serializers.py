from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from src.libs.get_context import get_user_by_context
from src.libs.messages import UNKNOWN_ERROR
from src.user.constants import SYSTEM_USER_ROLE
from src.user.utils.verification import send_user_forget_password_email
from src.user.validators import validate_image

from .messages import (
    ACCOUNT_DISABLED,
    ACCOUNT_NOT_FOUND,
    ALREADY_VERIFIED,
    INVALID_CREDENTIALS,
    INVALID_OTP,
    INVALID_PASSWORD,
    LOGIN_SUCCESS,
    OLD_PASSWORD_INCORRECT,
    OTP_EXPIRED,
    PASSWORDS_NOT_MATCH,
    SAME_OLD_NEW_PASSWORD,
)
from .models import (
    Permission,
    Role,
    User,
    UserAccountVerification,
    UserForgetPasswordRequest,
)
from .utils.generators import generate_secure_otp


class UserPermissionsSerializer(serializers.ModelSerializer):
    main_module = serializers.ReadOnlyField(source="permission_category.main_module.id")
    main_module_name = serializers.ReadOnlyField(
        source="permission_category.main_module.name",
    )
    permission_category_name = serializers.ReadOnlyField(
        source="permission_category.name",
    )

    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "codename",
            "permission_category",
            "permission_category_name",
            "main_module",
            "main_module_name",
        ]


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "codename"]


class UserLoginSerializer(serializers.ModelSerializer):
    """User Login Serializer"""

    persona = serializers.CharField(
        required=True,
        write_only=True,
        help_text="An identifier for the user, such as username or email.",
    )
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ["password", "persona"]

    def validate(self, attrs):
        persona = attrs.get("persona")
        password = attrs.pop("password")

        user = self.get_user(persona)

        # Validation Functions
        self.check_password(user, password)
        self.check_user_status(user)
        self.check_system_user(user)

        roles = UserRoleSerializer(user.roles.filter(is_active=True), many=True).data
        permissions = UserPermissionsSerializer(
            user.get_all_permissions(),
            many=True,
        ).data

        # save the last login timestamp
        user.last_login = timezone.now()
        user.save()

        return {
            "message": LOGIN_SUCCESS,
            "status": "success",
            "id": user.id,
            "is_superuser": user.is_superuser,
            "is_email_verified": user.is_email_verified,
            "is_phone_verified": user.is_phone_verified,
            "phone_no": user.phone_no,
            "photo": self.get_photo(user),
            "email": user.email,
            "tokens": user.tokens,
            "full_name": user.get_full_name(),
            "roles": roles,
            "permissions": permissions,
        }

    def get_photo(self, user: User) -> str | None:
        request = self.context.get("request")
        if user.photo:
            return request.build_absolute_uri(user.photo.url)
        return None

    def get_user(self, persona: str) -> User:
        try:
            if "@" in persona:
                user = User.objects.get(email=persona, is_archived=False)
            else:
                user = User.objects.get(username=persona, is_archived=False)
        except User.DoesNotExist as err:
            raise serializers.ValidationError({"persona": INVALID_CREDENTIALS}) from err
        return user

    def check_password(self, user: str, password: str) -> None:
        if not user.check_password(password):
            raise serializers.ValidationError({"password": INVALID_PASSWORD})

    def check_system_user(self, user: User) -> None:
        if not user.is_superuser:
            try:
                system_user_role = Role.objects.get(codename=SYSTEM_USER_ROLE)
            except Role.DoesNotExist as err:
                raise serializers.ValidationError({"error": UNKNOWN_ERROR}) from err

            # Fetch all roles associated with the user
            user_roles = user.roles.filter(is_active=True).values_list("id", flat=True)

            if system_user_role.id not in user_roles:
                raise serializers.ValidationError({"persona": INVALID_CREDENTIALS})

    def check_user_status(self, user: User) -> None:
        if not user.is_active or user.is_archived:
            raise serializers.ValidationError({"persona": ACCOUNT_DISABLED})


class UserLogoutSerializer(serializers.Serializer):
    """User Logout Serializer"""

    refresh = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={"required": "Refresh token is required."},
    )
    message = serializers.CharField(read_only=True)

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
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "photo",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "phone_no",
            "email",
            "is_superuser",
            "date_joined",
            "last_login",
            "is_active",
            "is_email_verified",
            "is_phone_verified",
            "roles",
        ]

    def get_full_name(self, obj) -> str:
        return obj.get_full_name()

    def get_roles(self, obj) -> list:
        user_roles = obj.roles.filter(is_active=True)
        return [user_role.name for user_role in user_roles]


class UserChangePasswordSerializer(serializers.Serializer):
    """User Change Password Serializer"""

    old_password = serializers.CharField(max_length=128, required=True, write_only=True)
    new_password = serializers.CharField(
        max_length=128,
        required=True,
        validators=[validate_password],
        write_only=True,
    )
    confirm_password = serializers.CharField(
        max_length=128,
        required=True,
        write_only=True,
    )
    message = serializers.CharField(read_only=True)

    def validate(self, attrs):
        user = get_user_by_context(self.context)
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        # Check if old password matches
        if not user.check_password(old_password):
            raise serializers.ValidationError({"old_password": OLD_PASSWORD_INCORRECT})

        # Check if new password and old password are same
        if new_password == old_password:
            raise serializers.ValidationError({"new_password": SAME_OLD_NEW_PASSWORD})

        # Check if new password and confirm password match
        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": PASSWORDS_NOT_MATCH})

        return attrs


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """User Profile Update Serializer"""

    first_name = serializers.CharField(max_length=50, required=False)
    last_name = serializers.CharField(max_length=50, required=False)
    photo = serializers.ImageField(
        allow_null=True,
        required=False,
        validators=[validate_image],
    )
    phone_no = serializers.CharField(
        max_length=10,
        required=False,
        allow_blank=True,
        min_length=10,
    )

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "photo",
            "phone_no",
        ]

    def update(self, instance: User, validated_data):
        photo = validated_data.get("photo", None)

        # Update user details
        instance.first_name = (
            validated_data.get("first_name", instance.first_name).strip().title()
        )
        instance.last_name = (
            validated_data.get("last_name", instance.last_name).strip().title()
        )

        instance.phone_no = validated_data.get("phone_no", instance.phone_no)
        instance.updated_at = timezone.now()

        if "photo" in validated_data:
            if photo is not None:
                upload_path = instance.get_upload_path(
                    upload_path="instance/photos",
                    filename=photo.name,
                )
                instance.photo.delete(save=False)  # Remove the old file
                instance.photo.save(upload_path, photo)
            else:
                instance.photo.delete(
                    save=True,
                )  # Delete the existing photo if photo is None

        instance.save()
        return instance


class UserForgetPasswordRequestSerializer(serializers.Serializer):
    """User Forget Password Request Serializer"""

    email = serializers.EmailField(required=True, write_only=True)
    message = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "")
        try:
            user = User.objects.get(email=email)
            if not user.is_active:
                raise serializers.ValidationError({"email": ACCOUNT_DISABLED})
            attrs["user"] = user
        except User.DoesNotExist as err:
            raise serializers.ValidationError(
                {"email": ACCOUNT_NOT_FOUND.format(email=email)},
            ) from err

        return attrs

    def create(self, validated_data):
        user = validated_data.pop("user", None)

        if user is not None:
            # Filter forget password requests by user and is_archived flag
            forget_password_requests = UserForgetPasswordRequest.objects.filter(
                user=user,
                is_archived=False,
            )

            # Archive the existing requests
            if forget_password_requests:
                forget_password_requests.update(is_archived=True)

            # Get new OTP
            otp = generate_secure_otp()
            UserForgetPasswordRequest.objects.create(
                user=user,
                token=otp,
                created_at=timezone.now(),
            )
            # Send the email to the user
            send_user_forget_password_email(
                recipient_email=validated_data["email"],
                otp=otp,
                request=self.context["request"],
            )

        return validated_data


class UserVerifyOTPSerializer(serializers.Serializer):
    """User OTP Verification Serializer"""

    otp = serializers.CharField(max_length=6, required=True, write_only=True)
    email = serializers.EmailField(required=True, write_only=True)
    message = serializers.CharField(read_only=True)

    def validate(self, attrs):
        otp = attrs.get("otp")
        email = attrs.get("email")

        try:
            forget_password_request = UserForgetPasswordRequest.objects.get(
                token=otp,
                is_archived=False,
                user__email=email,
            )
            now = timezone.now()
            delta = now - forget_password_request.created_at
            if delta > timedelta(minutes=settings.AUTH_LINK_EXP_TIME):
                raise serializers.ValidationError({"otp": OTP_EXPIRED})
        except UserForgetPasswordRequest.DoesNotExist as err:
            raise serializers.ValidationError({"otp": INVALID_OTP}) from err

        return attrs

    def create(self, validated_data):
        return ...


class UserForgetPasswordSerializer(serializers.Serializer):
    """User Forget Password Serializer"""

    otp = serializers.CharField(max_length=64, required=True, write_only=True)
    new_password = serializers.CharField(
        max_length=32,
        required=True,
        write_only=True,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(
        max_length=32,
        required=True,
        write_only=True,
    )
    message = serializers.CharField(read_only=True)

    def validate(self, attrs):
        otp = attrs.get("otp")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        try:
            forget_password_request = UserForgetPasswordRequest.objects.get(
                token=otp,
                is_archived=False,
            )
            attrs["forget_password_request"] = forget_password_request
            now = timezone.now()
            delta = now - forget_password_request.created_at
            if delta > timedelta(minutes=settings.AUTH_LINK_EXP_TIME):
                forget_password_request.is_archived = True
                forget_password_request.save()
                raise serializers.ValidationError({"otp": OTP_EXPIRED})
        except UserForgetPasswordRequest.DoesNotExist as err:
            raise serializers.ValidationError({"otp": INVALID_OTP}) from err

        attrs["user"] = forget_password_request.user
        old_password = attrs["user"].password

        # Check if new password and old password are same
        if check_password(new_password, old_password):
            raise serializers.ValidationError({"new_password": SAME_OLD_NEW_PASSWORD})

        # Check if new password and confirm password match
        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": PASSWORDS_NOT_MATCH})

        return attrs

    def create(self, validated_data):
        new_password = validated_data["new_password"]
        forget_password_request: UserForgetPasswordRequest = validated_data.get(
            "forget_password_request",
        )

        user: User = validated_data["user"]
        user.set_password(new_password)
        user.save()
        forget_password_request.is_archived = True
        forget_password_request.save()

        return validated_data


class UserVerifyAccountSerializer(serializers.Serializer):
    """User Verify Account Serializer"""

    otp = serializers.CharField(max_length=256, required=True)

    def validate(self, attrs):
        otp = attrs.get("otp")

        try:
            verification_request = UserAccountVerification.objects.get(
                token=otp,
                is_archived=False,
            )
            now = timezone.now()
            delta = now - verification_request.created_at

            if verification_request.user.is_email_verified:
                verification_request.is_archived = True
                verification_request.save()
                raise serializers.ValidationError({"email": ALREADY_VERIFIED})

            if delta > timedelta(minutes=settings.AUTH_LINK_EXP_TIME):
                verification_request.is_archived = True
                verification_request.save()
                raise serializers.ValidationError({"otp": OTP_EXPIRED})

        except UserAccountVerification.DoesNotExist as err:
            raise serializers.ValidationError({"otp": INVALID_OTP}) from err

        attrs["verification_request"] = verification_request

        return attrs

    def create(self, validated_data):
        verification_request: UserAccountVerification = validated_data[
            "verification_request"
        ]
        user_instance = verification_request.user
        user_instance.is_email_verified = True
        user_instance.save()
        verification_request.is_archived = True
        verification_request.save()
        return validated_data
