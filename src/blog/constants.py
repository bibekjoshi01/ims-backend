from enum import Enum

from django.utils.translation import gettext_lazy as _


# Blog Post Status
class PostStatus(Enum):
    PUBLISHED = "PUBLISHED"
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    REJECTED = "REJECTED"

    @classmethod
    def choices(cls):
        return [(key.value, _(key.name.capitalize())) for key in cls]


# Blog Post Visibility
class PostVisibility(Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    PASSWORD_PROTECTED = "PASSWORD-PROTECTED"  # noqa: S105

    @classmethod
    def choices(cls):
        return [(key.value, _(key.name.replace("_", " ").capitalize())) for key in cls]


# Blog Post Format
class PostFormat(Enum):
    STANDARD = "STANDARD"
    VIDEO = "VIDEO"
    GALLERY = "GALLERY"
    AUDIO = "AUDIO"
    QUOTE = "QUOTE"
    LINK = "LINK"

    @classmethod
    def choices(cls):
        return [(key.value, _(key.name.capitalize())) for key in cls]


# Blog Comment Status
class CommentStatus(Enum):
    MODERATION = "MODERATION"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    @classmethod
    def choices(cls):
        return [(key.value, _(key.name.capitalize())) for key in cls]
