import django_filters
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.filterset import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenRefreshView

from src.user.utils.verification import send_user_account_verification_email

from .models import User, UserAccountVerification, UserGroup
from .permissions import UserGroupSetupPermission, UserSetupPermission
from .serializers import (
    # User Group Serializer
    UserChangePasswordSerializer,
    UserForgetPasswordRequestSerializer,
    UserForgetPasswordSerializer,
    UserGroupCreateSerializer,
    UserGroupListSerializer,
    UserGroupPatchSerializer,
    UserGroupRetrieveSerializer,
    # User Serializers
    UserListSerializer,
    UserLoginSerializer,
    UserLogoutSerializer,
    UserPatchSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    UserRegisterSerializer,
    UserRetrieveSerializer,
    UserVerifyAccountSerializer,
)

# User Group Setup


class FilterForUserGroup(FilterSet):
    """Filters For User Group"""

    date = django_filters.DateFromToRangeFilter(field_name="created_at")
    name = django_filters.CharFilter(lookup_expr="iexact")
    codename = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = UserGroup
        fields = ["id", "date", "name", "codename", "is_active"]


class UserGroupViewSet(ModelViewSet):
    """
    ViewSet for managing CRUD operations for UserGroup model.
    """

    permission_classes = [UserGroupSetupPermission]
    queryset = UserGroup.objects.filter(
        ~Q(is_archived=True) | ~Q(is_system_managed=True),
    )
    serializer_class = UserGroupListSerializer
    filterset_class = FilterForUserGroup
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["name", "codename"]
    ordering = ["-created_at"]
    ordering_fields = ["id", "created_at", "codename"]
    http_method_names = ["get", "head", "options", "post", "patch"]

    def get_serializer_class(self):
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = UserGroupListSerializer
            else:
                serializer_class = UserGroupRetrieveSerializer
        if self.request.method == "POST":
            serializer_class = UserGroupCreateSerializer
        elif self.request.method == "PATCH":
            serializer_class = UserGroupPatchSerializer

        return serializer_class


# User Setup


class UserTokenRefreshView(TokenRefreshView):
    authentication_classes = [JWTAuthentication]


class FilterForUserViewSet(FilterSet):
    """Filters For User ViewSet"""

    username = django_filters.CharFilter(lookup_expr="iexact")
    date = django_filters.DateFromToRangeFilter(field_name="date_joined")

    class Meta:
        model = User
        fields = ["id", "username", "email", "phone_no", "groups"]


class UserViewSet(ModelViewSet):
    """
    ViewSet for managing CRUD operations for User model.
    """

    permission_classes = [UserSetupPermission]
    filter_class = FilterForUserViewSet
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    search_fields = ["mobile_no", "username", "email"]
    ordering_fields = ["-id", "first_name"]
    http_method_names = ["options", "head", "get", "patch", "post"]

    def get_queryset(self):
        system_user_group = get_object_or_404(UserGroup, codename="SYSTEM-USER")
        return User.objects.filter(
            is_superuser=False,
            is_staff=False,
            groups=system_user_group,
        )

    def get_serializer_class(self):
        serializer_class = UserListSerializer
        if self.request.method == "GET":
            if self.action == "list":
                serializer_class = UserListSerializer
            else:
                serializer_class = UserRetrieveSerializer

        if self.request.method == "POST":
            serializer_class = UserRegisterSerializer
        elif self.request.method == "PATCH":
            serializer_class = UserPatchSerializer
        return serializer_class


class UserLoginView(APIView):
    """User Login API View"""

    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request},
        )
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            is_email_verified = data["is_email_verified"]
            email = data["email"]
            is_superuser = data["is_superuser"]
            user_id = data["id"]

            if not is_email_verified and not is_superuser:
                verification_request = UserAccountVerification.objects.filter(
                    user_id=user_id,
                    is_archived=False,
                )
                # Archive the filtered requests
                verification_request.update(is_archived=True)
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


class UserVerifyAccountAPIView(APIView):
    """User Verify Account View"""

    permission_classes = [AllowAny]
    serializer_class = UserVerifyAccountSerializer

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


class UserLogoutView(APIView):
    """User LogOut View"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserLogoutSerializer

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


class UserProfileView(generics.RetrieveAPIView):
    """User Profile View"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return get_object_or_404(User, pk=self.request.user.pk)


class UserProfileUpdateView(generics.UpdateAPIView):
    """User Profile Update View"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer
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


class UserChangePasswordView(APIView):
    """Change Users Password View"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserChangePasswordSerializer

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


class UserForgetPasswordRequestView(APIView):
    """Forget Password Request View"""

    permission_classes = [AllowAny]
    serializer_class = UserForgetPasswordRequestSerializer

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


class UserForgetPasswordView(APIView):
    """User Forget Password View"""

    permission_classes = [AllowAny]
    serializer_class = UserForgetPasswordSerializer

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
