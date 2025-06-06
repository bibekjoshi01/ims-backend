from django.db import models
from django.utils.translation import gettext_lazy as _

from src.base.models import AbstractInfoModel


class Store(AbstractInfoModel):
    """
    Represents a physical or virtual store where inventory is stored
    and purchases are received.
    """

    name = models.CharField(
        max_length=100,
        verbose_name=_("Store Name"),
        help_text=_(
            "Name of the store or stock location (e.g., Main Branch, Warehouse 1)",
        ),
    )
    code = models.CharField(
        max_length=20,
        verbose_name=_("Store Code"),
        help_text=_("Unique short code to identify the store (e.g., MAIN, KTM01)"),
    )
    address = models.TextField(
        blank=True,
        verbose_name=_("Address"),
        help_text=_("Physical address of the store (optional)"),
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Contact Person"),
        help_text=_("Person responsible for managing the store"),
    )
    phone_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Phone number for store contact"),
    )

    class Meta:
        verbose_name = _("Store")
        verbose_name_plural = _("Stores")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"
