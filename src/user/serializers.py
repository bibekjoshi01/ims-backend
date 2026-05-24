from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from src.user.models import User


class UserLoginSerializer(serializers.ModelSerializer):
    """User Login Serializer"""

    persona = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = User
        fields = ["password", "persona"]

    def validate(self, attrs):
        persona = attrs.get("persona").strip().lower()
        password = attrs.pop("password")

        user = self.get_user(persona)

        if not user:
            error_message = "Invalid credentials"
            raise serializers.ValidationError({"persona": error_message})

        self.check_password(user, password)
        self.check_user_status(user)
        self.check_system_user(user)

        user.save()

        return {
            "message": "Logged in Successfully",
            "status": "success",
            "id": user.id,
            "is_superuser": user.is_superuser,
            "email": user.email,
            "username": user.username,
            "tokens": user.tokens,
        }

    def get_user(self, persona):
        try:
            if "@" in persona:
                user = User.objects.filter(email=persona, is_archived=False).first()
            else:
                user = User.objects.filter(username=persona, is_archived=False).first()
        except User.DoesNotExist as err:
            raise serializers.ValidationError({"persona": "Invalid Credentials"}) from err
        return user

    def check_password(self, user, password):
        if not user.check_password(password):
            raise serializers.ValidationError({"password": "Invalid Password"})

    def check_system_user(self, user):
        if user.is_superuser is not True:
            if not user.roles.filter(codename="SYSTEM-USER").exists():
                raise serializers.ValidationError({"persona": "Invalid Credentials"})

    def check_user_status(self, user):
        if not user.is_superuser:
            if not user.is_active or user.is_archived:
                raise serializers.ValidationError({"persona": "Account disable"})


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
