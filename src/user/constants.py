from typing import TypedDict

from src.base.constants import BaseEnum


class Genders(BaseEnum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    RATHER_NOT_TO_SAY = "RATHER_NOT_TO_SAY"


SYSTEM_USER_ROLE = "SYSTEM-USER"


class VerificationTypes(BaseEnum):
    OTP = "OTP"
    LINK = "LINK"
