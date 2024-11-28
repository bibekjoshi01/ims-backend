from enum import Enum
from typing import TypedDict, Optional

from django.utils.translation import gettext_lazy as _

class AuthProviders(Enum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"
    LINKEDIN = "LINKEDIN"
    APPLE = "APPLE"

    @classmethod
    def choices(cls):
        return [(key.value, _(key.name.capitalize())) for key in cls]


class UserInfo(TypedDict):
    type: str
    first_name: str
    last_name: str
    full_name: str
    photo: Optional[str]  # None or a string (e.g., URL)
    email: str
