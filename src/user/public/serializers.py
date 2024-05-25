from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from src.cart.models import Cart
from src.libs.get_context import get_user_by_context
from src.user.models import (
    User,
    UserAccountVerification,
    UserForgetPasswordRequest,
    UserGroup,
    UserPermission,
)
from src.user.utils.generate_username import generate_unique_user_username
from src.user.utils.verification import (
    send_user_account_verification_email,
    send_user_forget_password_email,
)
from src.user.validators import validate_image


class PublicUserSignUpSerializer(serializers.ModelSerializer):
    """Public User SignUp Serializer"""

    first_name = serializers.CharField(max_length=50, required=True)
    middle_name = serializers.CharField(max_length=50, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=True)
    phone_no = serializers.CharField(max_length=10, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        max_length=16,
        write_only=True,
        min_length=8,
        required=True,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(
        max_length=16,
        write_only=True,
        min_length=8,
        required=True,
    )
    has_accepted_terms = serializers.BooleanField(default=False)

    class Meta:
        model = User
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "phone_no",
            "password",
            "confirm_password",
            "has_accepted_terms",
        ]

    def validate(self, attrs):
        if not attrs["has_accepted_terms"]:
            raise serializers.ValidationError(
                {"has_accepted_terms": "You must accept our Terms of Service."},
            )

        if User.objects.filter(email=attrs["email"]).exists():
            message = "User already exists with this email. Try LogIn !"
            raise serializers.ValidationError(
                {"email": message},
            )

        if User.objects.filter(phone_no=attrs["phone_no"]).exists():
            message = "User already exists with this mobile no. Try LogIn !"
            raise serializers.ValidationError(
                {"phone_no": message},
            )

        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."},
            )

        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        email = validated_data["email"]

        username = generate_unique_user_username(user_type="website_user")

        user_instance = User.objects.create_website_user(
            first_name=validated_data["first_name"].title(),
            middle_name=validated_data.get("middle_name", "").title(),
            last_name=validated_data["last_name"].title(),
            phone_no=validated_data["phone_no"],
            password=validated_data["password"],
            email=email,
            username=username,
        )
        user_instance.save()

        # Create a cart for the website user
        Cart.objects.create(user=user_instance)

        send_user_account_verification_email(
            recipient_email=email,
            user_id=user_instance.id,
            request=self.context["request"],
        )

        return user_instance

    def to_representation(self, instance):
        return {
            "type": "Account Verification.",
            "message": f"Verification Email Sent to {instance.email}.",
        }


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


class PublicUserLoginSerializer(serializers.ModelSerializer):
    """User Login Serializer"""

    persona = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ["persona", "password"]

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
        user_permissions = GetUserPermissionsSerializer(
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
            "user_permissions": user_permissions.data,
        }


class PublicUserLogoutSerializer(serializers.Serializer):
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


class PublicUserProfileSerializer(serializers.ModelSerializer):
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


class PublicUserChangePasswordSerializer(serializers.Serializer):
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


class PublicUserProfileUpdateSerializer(serializers.ModelSerializer):
    """User Profile Update Serializer"""

    first_name = serializers.CharField(max_length=50, required=False)
    middle_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50, required=False)
    photo = serializers.ImageField(
        allow_null=True,
        required=False,
        validators=[validate_image],
    )
    phone_no = serializers.CharField(max_length=10, required=False)

    class Meta:
        model = User
        fields = [
            "first_name",
            "middle_name",
            "last_name",
            "phone_no",
            "photo",
        ]

    def update(self, instance, validated_data):
        photo = validated_data.pop("photo", None)

        # Update user details
        instance.first_name = validated_data.get("first_name", "").strip().title()
        instance.middle_name = validated_data.get("middle_name", "").strip().title()
        instance.last_name = validated_data.get("last_name", "").strip().title()

        instance.phone_no = validated_data.get("phone_no", instance.phone_no)
        instance.updated_at = timezone.now()

        if photo:
            upload_path = instance.get_upload_path(
                upload_path="user/photos",
                filename=photo.name,
            )
            instance.photo.delete(save=False)  # Remove the old file
            instance.photo.save(upload_path, photo)

        instance.save()

        return instance


class PublicUserForgetPasswordRequestSerializer(serializers.Serializer):
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


class PublicUserForgetPasswordSerializer(serializers.Serializer):
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


class PublicUserVerifyAccountSerializer(serializers.Serializer):
    """Public User Verify Account Serializer"""

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
