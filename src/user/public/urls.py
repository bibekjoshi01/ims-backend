from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PublicUserChangePasswordView,
    PublicUserForgetPasswordRequestView,
    PublicUserForgetPasswordView,
    PublicUserLoginView,
    PublicUserLogoutView,
    PublicUserProfileUpdateView,
    PublicUserProfileView,
    PublicUserSignUpAPIView,
    PublicUserTokenRefreshView,
    PublicUserVerifyAccountAPIView,
)

router = DefaultRouter(trailing_slash=False)

urlpatterns = [
    path(
        "users/signup",
        PublicUserSignUpAPIView.as_view(),
        name="public_user_login",
    ),
    path("users/login", PublicUserLoginView.as_view(), name="public_user_login"),
    path("users/logout", PublicUserLogoutView.as_view(), name="public_user_logout"),
    path("users/profile", PublicUserProfileView.as_view(), name="public_user_profile"),
    path(
        "users/account/verify",
        PublicUserVerifyAccountAPIView.as_view(),
        name="public_verify_account",
    ),
    path(
        "users/profile/update",
        PublicUserProfileUpdateView.as_view(),
        name="public_user_profile_update",
    ),
    path(
        "users/token/refresh",
        PublicUserTokenRefreshView.as_view(),
        name="public_token_refresh",
    ),
    path(
        "users/change-password",
        PublicUserChangePasswordView.as_view(),
        name="public_user_change_password",
    ),
    path(
        "users/forget-password-request",
        PublicUserForgetPasswordRequestView.as_view(),
        name="public_user_forget_password_request",
    ),
    path(
        "users/forget-password",
        PublicUserForgetPasswordView.as_view(),
        name="public_user_forget_password",
    ),
    path("", include(router.urls)),
]
