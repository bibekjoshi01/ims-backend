import secrets
import string

from src.user.constants import PUBLIC_USER_ROLE, SYSTEM_USER_ROLE
from src.user.models import User


def generate_role_codename(user_group_name):
    """Generate User Group Codename"""
    return user_group_name.upper().replace(" ", "-")


def generate_unique_user_username(user_type: str, email: str | None) -> str:
    """
    Generate a unique username for a user based on the user type.
    User Types: system_user, public_user
    email: Email address of the user (optional)
    """

    type_temp = user_type
    if type_temp == SYSTEM_USER_ROLE:
        title = "SU"
    elif type_temp == PUBLIC_USER_ROLE:
        title = "PU"
    else:
        title = "UU"

    """Generate a unique username of 15 characters long."""
    chars = string.digits
    # Generate a random string of 10 characters long
    extra = "".join(secrets.choice(chars) for _ in range(10))
    if not email:
        username = f"{title}-{extra[5:]}-{extra[:5]}"
    else:
        username = email.split("@")[0] + extra[:5]

    # Check if the generated username already exists
    if User.objects.filter(username=username).exists():
        generate_unique_user_username(user_type, email=email)

    return username


def generate_strong_password():
    # Define the character sets for generating the password
    uppercase_letters = string.ascii_uppercase
    lowercase_letters = string.ascii_lowercase
    digits = string.digits
    special_characters = string.punctuation

    # Combine all character sets
    all_characters = uppercase_letters + lowercase_letters + digits + special_characters

    # Generate a strong password of 8 characters using secrets module
    return "".join(secrets.choice(all_characters) for _ in range(8))


def generate_secure_otp():
    """Generates a cryptographically secure 6-digit One-Time Password (OTP)."""
    return "".join(secrets.choice("0123456789") for _ in range(6))


def generate_secure_token(length: int = 32) -> str:
    """Generates a cryptographically secure URL-safe token."""
    # token_urlsafe(n) returns a string with ~1.3 * n length
    # So to get a token around 32 characters, use 24 bytes
    return secrets.token_urlsafe(length)
