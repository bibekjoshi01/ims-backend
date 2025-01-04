import secrets
import string

from src.user.models import User


def generate_role_codename(user_group_name):
    """Generate User Group Codename"""
    return user_group_name.upper().replace(" ", "-")


def generate_unique_user_username(user_type: str, email: str | None) -> str:
    type_temp = user_type
    if type_temp == "system_user":
        title = "SU"
    elif type_temp == "website_user":
        title = "WU"
    else:
        title = "NA"

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
