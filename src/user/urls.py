from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .auth_views import (
    UserChangePasswordView,
    UserDeleteAccountView,
    UserForgetPasswordRequestView,
    UserForgetPasswordView,
    UserLoginView,
    UserLogoutView,
    UserProfileUpdateView,
    UserProfileView,
    UserTokenRefreshView,
    UserVerifyAccountAPIView,
    UserVerifyOTPAPIView,
)
from .listing_apis.views import (
    MainModuleForRoleView,
    RoleForUserView,
    UserPermissionCategoryForRoleView,
    UserPermissionForRoleView,
)
from .views import RoleArchiveView, RoleViewSet, UserArchiveView, UserViewSet

router = DefaultRouter(trailing_slash=False)

router.register("users", UserViewSet, basename="users")
router.register("roles", RoleViewSet, basename="roles")

urlpatterns = [
    # User Authencation
    # ---------------------------------------------------------------------------------
    path("users/token/refresh", UserTokenRefreshView.as_view(), name="token_refresh"),
    path("users/login", UserLoginView.as_view(), name="user_login"),
    path("users/logout", UserLogoutView.as_view(), name="user_logout"),
    path(
        "users/account/verify",
        UserVerifyAccountAPIView.as_view(),
        name="verify_account",
    ),
    path("users/profile", UserProfileView.as_view(), name="user_profile"),
    path(
        "users/profile/update",
        UserProfileUpdateView.as_view(),
        name="user_profile_update",
    ),
    path(
        "users/account/delete",
        UserDeleteAccountView.as_view(),
        name="user_delete_account",
    ),
    path(
        "users/change-password",
        UserChangePasswordView.as_view(),
        name="user_change_password",
    ),
    path(
        "users/forget-password-request",
        UserForgetPasswordRequestView.as_view(),
        name="user_forget_password_request",
    ),
    path(
        "users/verify-otp",
        UserVerifyOTPAPIView.as_view(),
        name="user_verify_otp",
    ),
    path(
        "users/forget-password",
        UserForgetPasswordView.as_view(),
        name="user_forget_password",
    ),
    # User/Roles Setup
    # ----------------------------------------------------------------------------------
    path(
        "roles/<int:role_id>/archive",
        RoleArchiveView.as_view(),
        name="user_role_archive",
    ),
    path("users/<int:user_id>/archive", UserArchiveView.as_view(), name="user_archive"),
    # Listing APIs
    path("users/roles", RoleForUserView.as_view(), name="user_roles"),
    path(
        "roles/main-modules",
        MainModuleForRoleView.as_view(),
        name="main_modules",
    ),
    path(
        "roles/permissions",
        UserPermissionForRoleView.as_view(),
        name="permissions",
    ),
    path(
        "roles/permission-categories",
        UserPermissionCategoryForRoleView.as_view(),
        name="permission_categories",
    ),
    path("", include(router.urls)),
]
