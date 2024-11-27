from enum import Enum
from django.utils.translation import gettext_lazy as _

class ThirdPartyApps(Enum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"
    LINKEDIN = "LINKEDIN"
    APPLE = "APPLE"

    @classmethod
    def choices(cls):
        return [(key.value, _(key.name.capitalize())) for key in cls]

MAX_PUBLIC_POST_TAG_LIMIT = 4
MAX_PUBLIC_POST_CATEGORY_LIMIT = 2

GOOGLE_CLIENT_ID = "197523093421-7dd93s0jup4ulbfovkn2krvvun0k7lph.apps.googleusercontent.com"


