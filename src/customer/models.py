from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _

from src.base.models import AbstractInfoModel
from src.core.constants import Gender

from .constants import AddressLabel


class Customer(AbstractInfoModel):
    """Represents model to store information about customer"""

    full_name = models.CharField(
        max_length=255,
        verbose_name=_("Full Name"),
        help_text=_("Full name of the customer."),
    )
    customer_no = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        verbose_name=_("Customer Number"),
        help_text=_("Unique customer number, auto-generated."),
    )
    is_person = models.BooleanField(
        default=True,
        verbose_name=_("Is Person"),
        help_text=_("Is the customer is person or organization/company/group?"),
    )
    gender = models.CharField(
        _("Gender"),
        choices=Gender.choices(),
        max_length=20,
        default=Gender.NA.value,
        help_text=_("Customer gender in case of person."),
    )
    photo = models.ImageField(
        upload_to="customer/",
        null=True,
        blank=True,
        verbose_name=_("Photo"),
        help_text=_("Photo of the customer (optional)."),
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email"),
        help_text=_("Primary email address."),
    )
    phone_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Primary phone number."),
    )
    alt_phone_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Alternative Phone Number"),
        help_text=_("Alternative contact number."),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Any additional notes or information about the customer."),
    )

    class Meta:
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")
        ordering = ["-id"]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        if not self.customer_no:
            idf = "P" if self.is_person else "O"
            self.customer_no = self.generate_customer_no(idf)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_customer_no(idf: str):
        """
        Generates a unique customer number like: CUS-P/O-20250602-XYZ1
        """

        date_part = timezone.now().strftime("%Y%m%d")
        random_part = get_random_string(4).upper()
        return f"CUS-{idf}-{date_part}-{random_part}"


class CustomerAddress(AbstractInfoModel):
    """Stores address details related to a customer."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="addresses",
        verbose_name=_("Customer"),
        help_text=_("The customer this address belongs to."),
    )
    label = models.CharField(
        max_length=100,
        choices=AddressLabel.choices(),
        default=AddressLabel.DEFAULT.value,
        verbose_name=_("Label"),
        help_text=_("Optional label like 'Home', 'Office', etc."),
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address"),
        help_text=_("Full Address, e.g. Bhimdatta 10, Kanchanpur, Sudurpashim"),
    )

    class Meta:
        verbose_name = _("Customer Address")
        verbose_name_plural = _("Customer Addresses")
        ordering = ["-id"]

    def __str__(self):
        return f"{self.customer.full_name} - {self.label or 'Address'}"
