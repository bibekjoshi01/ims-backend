from django.utils.translation import gettext_lazy as _

ERROR_MESSAGES = {
    "account_disabled": _("Account Disabled."),
    "signin_failed": _("Unable to sign in. Please try again."),
    "provider_not_supported": _("This third-party provider is not supported."),
    "email_not_verified": _("Email verification failed."),
}
