from django.urls import include, path
from rest_framework.routers import DefaultRouter

from src.user.views import UserLoginView, UserLogoutView, UserTokenRefreshView

router = DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("account/token/refresh", UserTokenRefreshView.as_view(), name="user-token-refresh"),
    path("account/login", UserLoginView.as_view(), name="user-login"),
    path("account/logout", UserLogoutView.as_view(), name="user-logout"),
    path("", include(router.urls)),
]
