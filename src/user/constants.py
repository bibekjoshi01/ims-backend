from src.base.constants import BaseEnum


class Genders(BaseEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    RATHER_NOT_TO_SAY = "RATHER_NOT_TO_SAY"


class AuthProviders(BaseEnum):
    BY_EMAIL = "BY_EMAIL"
    GOOGLE = "GOOGLE"
    APPLE = "APPLE"


SYSTEM_USER_ROLE = "SYSTEM-USER"
