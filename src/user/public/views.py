from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView

from src.user.models import User, UserAccountVerification
from src.user.public.permissions import WebsiteUserBasePermission
from src.user.throttling import LoginThrottle
from src.user.utils.verification import send_user_account_verification_email

from .serializers import (
    PublicUserChangePasswordSerializer,
    PublicUserForgetPasswordRequestSerializer,
    PublicUserForgetPasswordSerializer,
    PublicUserLoginSerializer,
    PublicUserLogoutSerializer,
    PublicUserProfileSerializer,
    PublicUserProfileUpdateSerializer,
    PublicUserSignUpSerializer,
    PublicUserVerifyAccountSerializer,
)


class PublicUserTokenRefreshView(TokenRefreshView):
    """Get AccessToken View"""

    authentication_classes = [JWTAuthentication]


class PublicUserSignUpAPIView(generics.CreateAPIView):
    """
    User SignUp API View.
    """

    permission_classes = [AllowAny]
    queryset = User.objects.all()
    serializer_class = PublicUserSignUpSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        return super().perform_create(serializer)


class PublicUserLoginView(APIView):
    """User Login API View"""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = PublicUserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            is_email_verified = data["is_email_verified"]
            email = data["email"]
            user_id = data["id"]

            if not is_email_verified:
                verification_request = UserAccountVerification.objects.filter(
                    user_id=user_id,
                    is_archived=False,
                )
                # Archive the filtered requests
                verification_request.update(is_archived=True)
                # Send the account verification email
                send_user_account_verification_email(
                    recipient_email=email,
                    user_id=user_id,
                    request=request,
                )
                response_message = (
                    f"Verification mail sent to : {email} valid for 10 minutes."
                )
                return Response(
                    {"message": response_message},
                    status=status.HTTP_200_OK,
                )
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserVerifyAccountAPIView(APIView):
    """User Verify Account View"""

    permission_classes = [AllowAny]
    serializer_class = PublicUserVerifyAccountSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Your Account Verified Successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserLogoutView(APIView):
    """User LogOut View"""

    permission_classes = [WebsiteUserBasePermission]
    serializer_class = PublicUserLogoutSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Logout Successfull"},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserProfileView(generics.RetrieveAPIView):
    """User Profile View"""

    permission_classes = [WebsiteUserBasePermission]
    serializer_class = PublicUserProfileSerializer

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.pk)


class PublicUserProfileUpdateView(generics.UpdateAPIView):
    """User Profile Update View"""

    permission_classes = [WebsiteUserBasePermission]
    serializer_class = PublicUserProfileUpdateSerializer
    http_method_names = ["patch"]

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.pk)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            self.perform_update(serializer)
            serializer.save()
            return Response(
                {"message": "Profile Updated Successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserChangePasswordView(APIView):
    """Change Users Password View"""

    permission_classes = [WebsiteUserBasePermission]
    serializer_class = PublicUserChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            user = request.user
            new_password = serializer.validated_data.get("new_password")

            # Set new password and save user
            user.set_password(new_password)
            user.save()

            return Response(
                {"message": "Password changed successfully"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserForgetPasswordRequestView(APIView):
    """Forget Password Request View"""

    permission_classes = [AllowAny]
    serializer_class = PublicUserForgetPasswordRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            validated_data = serializer.validated_data
            email = validated_data["email"]
            serializer.save()
            response_message = (
                f"Password Reset Link Sent To Email: {email} valid for 10 minutes."
            )
            return Response(
                {"message": response_message},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicUserForgetPasswordView(APIView):
    """User Forget Password View"""

    permission_classes = [AllowAny]
    serializer_class = PublicUserForgetPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(
                {"message": "Password Changed Successfully."},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
