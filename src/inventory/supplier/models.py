from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from src.base.models import AbstractInfoModel

User = get_user_model()


class InvSupplier(AbstractInfoModel):
    user = models.OneToOneField(
        User,
        on_delete=models.PROTECT,
        related_name="inv_supplier",
        verbose_name=_("User"),
        help_text=_("Link to the user account of the supplier (optional)."),
        null=True,
        blank=True,
    )
    opening_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Opening Balance"),
        help_text=_("Initial balance amount (default: 0.00)."),
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Remarks"),
        help_text=_("Optional remarks about the supplier."),
    )

    class Meta:
        verbose_name = _("Inventory Supplier")
        verbose_name_plural = _("Inventory Suppliers")
        ordering = ["-id"]

    def __str__(self):
        return f"Supplier: {self.user.get_full_name() or self.user.email}"
