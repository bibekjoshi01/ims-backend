from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .listing_apis.views import (
    MainModuleForUserGroupsView,
    UserGroupsForUserView,
    UserPermissionCategoryForUserGroupsView,
    UserPermissionForUserGroupsView,
)
from .views import (
    UserChangePasswordView,
    UserForgetPasswordRequestView,
    UserForgetPasswordView,
    UserGroupViewSet,
    UserLoginView,
    UserLogoutView,
    UserProfileUpdateView,
    UserProfileView,
    UserTokenRefreshView,
    UserVerifyAccountAPIView,
    UserViewSet,
)

router = DefaultRouter(trailing_slash=False)

router.register("users", UserViewSet, basename="users")
router.register("user-groups", UserGroupViewSet, basename="user_groups")

urlpatterns = [
    path("users/token/refresh", UserTokenRefreshView.as_view(), name="token_refresh"),
    path("users/login", UserLoginView.as_view(), name="user_login"),
    path(
        "users/account/verify",
        UserVerifyAccountAPIView.as_view(),
        name="verify_account",
    ),
    path("users/logout", UserLogoutView.as_view(), name="user_logout"),
    path("users/profile", UserProfileView.as_view(), name="user_profile"),
    path(
        "users/profile/update",
        UserProfileUpdateView.as_view(),
        name="user_profile_update",
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
        "users/forget-password",
        UserForgetPasswordView.as_view(),
        name="user_forget_password",
    ),
    # Listing APIs
    path("users/user-group", UserGroupsForUserView.as_view(), name="user_group"),
    path(
        "user-groups/main-modules",
        MainModuleForUserGroupsView.as_view(),
        name="main_modules",
    ),
    path(
        "user-groups/user-permissions",
        UserPermissionForUserGroupsView.as_view(),
        name="user_permissions",
    ),
    path(
        "user-groups/user-permission-categories",
        UserPermissionCategoryForUserGroupsView.as_view(),
        name="user_permission_categories",
    ),
    path("", include(router.urls)),
]
