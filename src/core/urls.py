from rest_framework import routers

from .views import (
    EmailConfigViewSet,
    OrganizationSetupViewSet,
    ThirdPartyCredentialViewSet,
)

router = routers.DefaultRouter(trailing_slash=False)

router.register("organization-details", OrganizationSetupViewSet)
router.register("third-party-creds", ThirdPartyCredentialViewSet)
router.register("email-configs", EmailConfigViewSet)

list_urls = []

urlpatterns = [*list_urls, *router.urls]
