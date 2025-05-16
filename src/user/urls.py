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
    # User Auth
    # ---------------------------------------------------------------------------------
    path("auth/login", UserLoginView.as_view(), name="user-login"),
    path("auth/logout", UserLogoutView.as_view(), name="user-logout"),
    path("auth/token/refresh", UserTokenRefreshView.as_view(), name="token-refresh"),
    path(
        "auth/verify",
        UserVerifyAccountAPIView.as_view(),
        name="verify-account",
    ),
    path(
        "auth/forget-password-request",
        UserForgetPasswordRequestView.as_view(),
        name="user-forget-password-request",
    ),
    path(
        "auth/forget-password",
        UserForgetPasswordView.as_view(),
        name="user-forget-password",
    ),  
    path("account/profile", UserProfileView.as_view(), name="user-profile"),
    path(
        "account/profile/update",
        UserProfileUpdateView.as_view(),
        name="user-profile-update",
    ),
    path(
        "account/delete",
        UserDeleteAccountView.as_view(),
        name="user-delete-account",
    ),
    path(
        "account/change-password",
        UserChangePasswordView.as_view(),
        name="user-change-password",
    ),
    # User/Roles Setup
    # ----------------------------------------------------------------------------------
    path(
        "roles/<int:role_id>/archive",
        RoleArchiveView.as_view(),
        name="user-role-archive",
    ),
    path("users/<int:user_id>/archive", UserArchiveView.as_view(), name="user-archive"),
    # Listing APIs
    # ----------------------------------------------------------------------------------
    path("users/roles", RoleForUserView.as_view(), name="user-roles"),
    path(
        "roles/main-modules",
        MainModuleForRoleView.as_view(),
        name="main-modules",
    ),
    path(
        "roles/permissions",
        UserPermissionForRoleView.as_view(),
        name="permissions",
    ),
    path(
        "roles/permission-categories",
        UserPermissionCategoryForRoleView.as_view(),
        name="permission-categories",
    ),
    path("", include(router.urls)),
]
