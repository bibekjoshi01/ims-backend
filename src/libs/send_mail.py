from smtplib import SMTPException

from celery import shared_task
from django.contrib.sites.shortcuts import get_current_site
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.templatetags.static import static

from src.core.models import EmailConfig
from src.libs.loggers import email_logger as logger


def get_basic_urls(request):
    """
    Utility function to generate basic URLs using the current site information.
    Returns a dictionary with URLs for social media icons and logo.
    """
    # Initial URLs Value
    basic_urls = {
        "origin_url": "",
        "logo": "",
        "facebook_icon": "",
        "instagram_icon": "",
        "linkedin_icon": "",
        "youtube_icon": "",
    }

    try:
        # Get current site information
        current_site = get_current_site(request)
        origin_url = request.headers.get("origin", "")
        domain = current_site.domain
        base_static_url = f'https://{domain}{static("images")}'

        if not origin_url:
            logger.warning("Origin URL is missing in the request headers.")

        basic_urls["logo"] = f"{base_static_url}/logo.jpg"
        basic_urls["facebook_icon"] = f"{base_static_url}/icons/facebook.png"
        basic_urls["instagram_icon"] = f"{base_static_url}/icons/instagram.png"
        basic_urls["linkedin_icon"] = f"{base_static_url}/icons/linkedin.png"
        basic_urls["youtube_icon"] = f"{base_static_url}/icons/twitter.png"
        basic_urls["origin_url"] = origin_url

        if not current_site or not current_site.domain:
            logger.warning("Site domain configuration is missing.")
        else:
            return basic_urls

    except ImproperlyConfigured:
        logger.exception("Site domain configuration error")
    except KeyError:
        logger.exception("Missing expected data")
    except (Exception, ValueError):
        logger.exception("Failed to generate basic URLs")

    return basic_urls


def get_email_config(email_type: str):
    """Get Email Configs Based on mail type"""

    cache_key = f"email_config_{email_type}"
    config = cache.get(cache_key)

    if not config:
        config_ins = EmailConfig.objects.filter(email_type=email_type).first()

        if config_ins:
            config = {
                "EMAIL_HOST": config_ins.email_host,
                "EMAIL_USE_TLS": config_ins.email_use_tls,
                "EMAIL_USE_SSL": config_ins.email_use_ssl,
                "EMAIL_PORT": config_ins.email_port,
                "EMAIL_HOST_USER": config_ins.email_host_user,
                "EMAIL_HOST_PASSWORD": config_ins.email_host_password,
                "DEFAULT_FROM_EMAIL": config_ins.default_from_email,
                "SERVER_EMAIL": config_ins.server_mail,
            }
            cache.set(cache_key, config, timeout=3600)

    if not config:
        # Log an error message when no credentials are found
        logger.error("No email configuration found for email_type: %s", email_type)

    return config


@shared_task(bind=True, max_retries=3)
def _send_email(
    self,
    subject,
    body,
    template_name,
    context,
    recipient_email,
    email_type="INFO",
):
    email_config = get_email_config(email_type=email_type)
    if not email_config:
        logger.error("Email configuration is missing for email_type: %s", email_type)
        return False

    try:
        connection = get_connection(
            host=email_config["EMAIL_HOST"],
            port=email_config["EMAIL_PORT"],
            username=email_config["EMAIL_HOST_USER"],
            password=email_config["EMAIL_HOST_PASSWORD"],
            use_tls=email_config["EMAIL_USE_TLS"],
            use_ssl=email_config["EMAIL_USE_SSL"],
        )
    except (Exception, ConnectionError, ValueError) as exc:
        logger.exception("Failed to create SMTP connection: %s")
        self.retry(exc=exc)  # Retry the task with exponential backoff
        return False

    # Render the email template
    try:
        email_template = render_to_string(f"{template_name}.html", context)
    except (Exception, KeyError, TemplateDoesNotExist):
        logger.exception("Failed to render email template: %s")
        return False

    # Prepare email
    mail = EmailMultiAlternatives(
        subject,
        body,
        from_email=email_config["DEFAULT_FROM_EMAIL"],
        to=[recipient_email],
        connection=connection,
    )

    # Attach the HTML version of the email if available
    if email_template:
        mail.attach_alternative(email_template, "text/html")

    # Send email
    try:
        mail.send(fail_silently=False)
        logger.info("Email sent successfully to %s", recipient_email)
    except (Exception, TimeoutError, SMTPException, ConnectionError) as exc:
        logger.exception("Failed to send email to %s", recipient_email)
        self.retry(exc=exc)  # Retry on failure
        return False

    return True
