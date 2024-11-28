from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PublicUserSignInAPIView,
)

router = DefaultRouter(trailing_slash=False)

urlpatterns = [
    path(
        "users/signin",
        PublicUserSignInAPIView.as_view(),
        name="public_user_signup",
    ),
    path("", include(router.urls)),
]
