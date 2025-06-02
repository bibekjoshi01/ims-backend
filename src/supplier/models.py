from django.db import models
from django.utils.translation import gettext_lazy as _

from src.base.models import AbstractInfoModel


class Supplier(AbstractInfoModel):
    """Represents a supplier that provides inventory products."""

    name = models.CharField(
        max_length=255,
        verbose_name=_("Supplier Name"),
        help_text=_("Name of the supplier company or individual."),
    )
    contact_person = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Contact Person"),
        help_text=_("Full name of the main contact person."),
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email Address"),
        help_text=_("Email for communication and invoices."),
    )
    phone_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Phone number of the supplier."),
    )
    alt_phone_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Alternate Phone"),
        help_text=_("Alternate contact number."),
    )
    address = models.TextField(
        blank=True,
        verbose_name=_("Address"),
        help_text=_("Supplier's physical or mailing address."),
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Country"),
        help_text=_("Country of the supplier."),
    )
    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
        help_text=_("Official website of the supplier, if any."),
    )
    tax_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Tax ID / VAT Number"),
        help_text=_("Tax registration number for accounting."),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional remarks or information about the supplier."),
    )

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ["-id"]

    def __str__(self):
        return f"{self.name} ({self.contact_person})"
