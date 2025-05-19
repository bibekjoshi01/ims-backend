from django.utils.translation import gettext_lazy as _

# General Messages
LOGIN_SUCCESS = _("You have successfully logged in.")
LOGOUT_SUCCESS = _("You have successfully logged out.")
INVALID_CREDENTIALS = _("Invalid credentials. Please try again.")
PROFILE_UPDATED = _("Profile updated successfully.")
ACCOUNT_ARCHIVED = _("Account deleted successfully.")

# User Validation Messages
USER_NOT_FOUND = _("User not found.")
USER_ARCHIVED = _("User archived successfully.")
USER_CREATED = _("User registered successfully.")
USER_UPDATED = _("User updated successfully.")
USER_ERRORS = {
    "USERNAME_EXISTS": _("This username is already taken."),
    "EMAIL_EXISTS": _("An USER with this email address already exists."),
    "PHONE_EXISTS": _("A user with this phone number already exists."),
    "MISSING_ROLES": _("Please select at least one user ROLE."),
}

# User Role Validation Messages
USER_ROLE_NOT_FOUND = _("User role not found.")
USER_ROLE_ARCHIVED = _("User role archived successfully.")
USER_ROLE_CREATED = _("User role registered successfully.")
USER_ROLE_UPDATED = _("User role updated successfully.")
USER_ROLE_ERRORS = {
    "ROLE_NAME": _("User role with name {name} already exists."),
}

# flake8: noqa
INVALID_PASSWORD = _("Incorrect password. Please try again.")
ACCOUNT_DISABLED = _(
    "Your account has been disabled. Please contact support for assistance."
)
VERIFICATION_EMAIL_SENT = _(
    "A verification email has been sent to {email}. It is valid for 10 minutes."
)
ACCOUNT_VERIFIED = _("Your Account Verified Successfully.")
OTP_VERIFIED = _("Link Verified Successfully.")
ACCOUNT_NOT_FOUND = _("Account with email {email} do not exists.")
PASSWORD_RESET_LINK_SENT = _(
    "A link has been sent to {email}. It is valid for 10 minutes."
)
PASSWORD_CHANGED = _("Password changed successfully.")
OLD_PASSWORD_INCORRECT = _("Incorrect old password.")
PASSWORDS_NOT_MATCH = _("New password and confirm password do not match.")
SAME_OLD_NEW_PASSWORD = _("New password must be different from old password.")
LINK_EXPIRED = _("Link has expired. Please try again.")
INVALID_LINK = _("Invalid link. Please try again.")
ACCOUNT_ALREADY_VERIFIED = _("Account already verified. Please log in.")
