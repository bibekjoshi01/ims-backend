import secrets

from django.contrib.sites.shortcuts import get_current_site
from django.templatetags.static import static
from django.utils import timezone
from rest_framework import serializers

from src.libs.send_mail import _send_email
from src.user.models import (
    User,
    UserAccountVerification,
    UserForgetPasswordRequest,
)


def send_user_forget_password_email(recipient_email, user_id, request):
    current_site = get_current_site(request)
    origin_url = request.headers.get("origin")
    lock_url = f'https://{current_site.domain}{static("images/icons/lock.png")}'

    try:
        user = User.objects.get(id=user_id)
        token = secrets.token_hex(32)
        subject = "Forget Password"
        body = "Account Information"
        email_template_name = "user/forget_password"
        reset_password_url = f"{origin_url}/forget-password/{token}"
        email_context = {
            "reset_password_url": reset_password_url,
            "lock_url": lock_url,
            "request": request,
        }
        sent_successfully = _send_email(
            subject,
            body,
            email_template_name,
            email_context,
            recipient_email,
        )
        if sent_successfully:
            UserForgetPasswordRequest.objects.create(
                user=user,
                token=token,
                created_at=timezone.now(),
                is_archived=False,
            )
    except User.DoesNotExist:
        raise serializers.ValidationError({"user_id": "Invalid User ID."}) from None
    except Exception as err:
        raise serializers.ValidationError(
            {"error": f"Unknown Error Occured. Try Again !{err}"},
        ) from err


def send_user_account_verification_email(recipient_email, user_id, request):
    current_site = get_current_site(request)
    origin_url = request.headers.get("origin")
    lock_url = f'https://{current_site.domain}{static("images/icons/lock.png")}'

    try:
        user = User.objects.get(id=user_id)
        token = secrets.token_hex(32)
        subject = "Account Verification"
        body = "Account Information"
        email_template_name = "user/account_verification"
        verification_url = f"{origin_url}/verify-account/{token}"
        email_context = {
            "verification_url": verification_url,
            "lock_url": lock_url,
            "request": request,
        }
        sent_successfully = _send_email(
            subject,
            body,
            email_template_name,
            email_context,
            recipient_email,
        )
        if sent_successfully:
            UserAccountVerification.objects.create(
                user=user,
                token=token,
                created_at=timezone.now(),
                is_archived=False,
            )
    except User.DoesNotExist:
        raise serializers.ValidationError({"user_id": "Invalid User ID."}) from None
    except Exception as err:
        raise serializers.ValidationError(
            {"error": "Unknown Error Occured. Try Again !"},
        ) from err
