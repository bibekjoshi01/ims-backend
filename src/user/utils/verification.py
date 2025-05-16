from django.contrib.sites.shortcuts import get_current_site
from django.templatetags.static import static
from rest_framework import serializers

from src.libs.messages import UNKNOWN_ERROR
from src.libs.send_mail import _send_email, get_basic_urls


def send_user_forget_password_email(recipient_email: str, token: str, request):
    current_site = get_current_site(request)
    lock_url = f'https://{current_site.domain}{static("images/icons/lock.png")}'

    try:
        subject = "Forget Password"
        body = "Account Information"
        email_template_name = "user/forget_password"
        email_context = {
            "token": token,
            "lock_url": lock_url,
            "basic_urls": get_basic_urls(request),
        }
        _send_email.delay(
            subject,
            body,
            email_template_name,
            email_context,
            recipient_email,
        )

    except Exception as err:
        raise serializers.ValidationError({"error": UNKNOWN_ERROR}) from err


def send_user_account_verification_email(recipient_email: str, token: str, request):
    current_site = get_current_site(request)
    lock_url = f'https://{current_site.domain}{static("images/icons/lock.png")}'

    try:
        subject = "Account Verification"
        body = "Account Information"
        email_template_name = "user/account_verification"
        email_context = {
            "token": token,
            "lock_url": lock_url,
            "basic_urls": get_basic_urls(request),
        }
        _send_email.delay(
            subject,
            body,
            email_template_name,
            email_context,
            recipient_email,
        )

    except Exception as err:
        raise serializers.ValidationError({"error": UNKNOWN_ERROR}) from err
