from django.utils.translation import gettext_lazy as _

# Blog Post Status
POST_STATUS = (
    ("PUBLISHED", _("Published")),
    ("DRAFT", _("Draft")),
    ("SCHEDULED", _("Scheduled")),
    ("REJECTED", _("Rejected")),
)

# Blog Post Visibility
POST_VISIBILITY = (
    ("PUBLIC", _("Public")),
    ("PRIVATE", _("Private")),
    ("PASSWORD-PROTECTED", _("Password Protected")),
)

# Blog Post Format
POST_FORMAT = (
    ("STANDARD", _("Standard")),
    ("VIDEO", _("Video")),
    ("GALLERY", _("Gallery")),
    ("AUDIO", _("Audio")),
    ("QUOTE", _("Quote")),
    ("LINK", _("Link")),
)

# Blog Comment Status
COMMENT_STATUS = (
    ("MODERATION", _("Moderation")),
    ("APPROVED", _("Approved")),
    ("REJECTED", _("Rejected")),
)
