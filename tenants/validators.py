from django.core.validators import RegexValidator

subdomain_validator = RegexValidator(
    regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    message=(
        "Subdomain may contain only lowercase letters, "
        "numbers, and single hyphens. "
        "It cannot start/end with hyphen or contain spaces."
    ),
)


RESERVED_SUBDOMAINS = {
    "www",
    "api",
    "admin",
    "app",
    "mail",
    "static",
    "media",
    "docs",
}
