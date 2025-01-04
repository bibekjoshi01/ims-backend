from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from src.base.models import AbstractInfoModel

from .constants import SocialMedias


class OrganizationSetup(AbstractInfoModel):
    """
    Basic Details about Website Organization,
    Can be Used For Any Global Purpose
    """

    name = models.CharField(
        _("Name"),
        max_length=255,
        help_text=_("Name of the organization"),
    )
    display_name = models.CharField(
        _("Display Name"),
        max_length=255,
        help_text=_("Display name of the organization"),
    )
    favicon = models.ImageField(
        _("Favicon"),
        upload_to="organization_setup",
        null=True,
        max_length=255,
        help_text=_("Favicon of the organization"),
    )
    tagline = models.CharField(
        _("Tagline"),
        max_length=255,
        blank=True,
        help_text=_("Tagline of the organization"),
    )
    logo_main = models.ImageField(
        _("Main Logo"),
        upload_to="organization_setup",
        null=True,
        max_length=255,
        help_text=_("Main logo of the organization"),
    )
    logo_alt = models.ImageField(
        _("Alternate Logo"),
        upload_to="organization_setup",
        null=True,
        help_text=_("Alternate logo of the organization"),
    )
    website_url = models.URLField(
        _("Website URL"),
        blank=True,
        help_text=_("URL of the organization's website"),
    )
    address = models.CharField(
        _("Address"),
        max_length=255,
        help_text=_("Address of the organization"),
    )
    email = models.EmailField(_("Email"), help_text=_("Email of the organization"))
    privacy_policy = models.TextField(
        _("Privacy Policy"),
        help_text=_("Privacy Policy of the organization (english)"),
    )
    cookie_policy = models.TextField(
        _("Cookie Policy"),
        help_text=_("Cookie Policy of the organization (french)"),
    )
    terms_of_use = models.TextField(_("Terms of Use"), blank=True)

    class Meta:
        verbose_name = _("Organization Detail")
        verbose_name_plural = _("Organization Details")

    def __str__(self) -> str:
        return self.display_name


class OrganizationSocialLink(AbstractInfoModel):
    """
    Social Media Links For Organization
    """

    organization = models.ForeignKey(
        OrganizationSetup,
        on_delete=models.CASCADE,
        related_name="social_media_links",
    )
    social_media = models.CharField(choices=SocialMedias.choices(), max_length=20)
    link = models.URLField()

    def __str__(self):
        return self.social_media


class ThirdPartyCredential(AbstractInfoModel):
    """
    Model to store information for third party credentials
    """

    GATEWAYS = (("GOOGLE", "Google"),)

    gateway = models.CharField(
        choices=GATEWAYS,
        max_length=20,
        unique=True,
        help_text="Select the payment gateway from the list (e.g., Google, Paypal).",
    )
    base_url = models.URLField(
        blank=True,
        help_text="Base URL for the payment gateway's API (e.g., https://api.paypal.com/).",
        validators=[
            RegexValidator(regex=r"^https://", message="URL must start with https://"),
        ],
    )
    client_id = models.CharField(
        blank=True,
        max_length=255,
        help_text=(
            "Unique client ID provided by",
            "the payment gateway for authentication.",
        ),
    )
    client_secret = models.CharField(
        blank=True,
        max_length=255,
        help_text="Client secret provided by the gateway.",
        validators=[MinLengthValidator(8)],
    )
    webhook_id = models.CharField(
        blank=True,
        max_length=255,
        help_text="webhook id/secret provided by the gateway.",
    )

    def __str__(self) -> str:
        return str(self.gateway)


class EmailConfig(AbstractInfoModel):
    """Model to store email configuration settings."""

    EMAIL_TYPES = (
        ("INFO", "Info"),
        ("SALES", "Sales"),
        ("SUPPORT", "Support"),
    )

    email_type = models.CharField(
        choices=EMAIL_TYPES,
        max_length=20,
        unique=True,
        default="INFO",
        help_text="Type of email (e.g. sales, info)",
    )
    email_host = models.CharField(
        max_length=255,
        default="smtp.gmail.com",
        help_text="SMTP server address",
    )
    email_use_tls = models.BooleanField(
        default=True,
        help_text="Use TLS for the email connection",
    )
    email_use_ssl = models.BooleanField(
        default=False,
        help_text="Use SSL for the email connection",
    )
    email_port = models.PositiveIntegerField(
        default=587,
        help_text="Port for the email server",
    )
    email_host_user = models.EmailField(help_text="Email host user")
    email_host_password = models.CharField(
        max_length=255,
        help_text="Email host password",
    )
    default_from_email = models.EmailField(help_text="Default 'from' email address")
    server_mail = models.EmailField(
        blank=True,
        help_text="Email address for server errors",
    )

    def __str__(self):
        return f"EmailConfig (ID: {self.id}) - {self.email_type}"

    class Meta:
        verbose_name = _("Email Configuration")
        verbose_name_plural = _("Email Configurations")
