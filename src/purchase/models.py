# Django Imports
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from src.base.models import AbstractInfoModel

# Project Imports
from src.blog.models import User
from src.core.models import AdditionalChargeType, PaymentMethod
from src.inventory.catalog.models import Item, ItemCategory
from src.libs.validators import validate_file_extension

from .constants import PayType, PurchaseType


class InvPurchaseMain(AbstractInfoModel):
    """Main record for a purchase transaction."""

    purchase_type = models.CharField(
        choices=PurchaseType.choices(),
        max_length=30,
        verbose_name=_("Purchase Type"),
        help_text=_("Type of purchase (e.g., purchase, return)."),
        db_index=True,
    )
    pay_type = models.CharField(
        choices=PayType.choices(),
        max_length=10,
        verbose_name=_("Payment Type"),
        help_text=_("Payment method used for this purchase."),
    )
    purchase_no = models.PositiveIntegerField(
        verbose_name=_("Purchase Number"),
        help_text=_("Sequential number for tracking the purchase."),
    )
    purchase_no_full = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Full Purchase Number"),
        help_text=_("A complete identifier including prefixes or codes."),
    )
    discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Discount Rate (%)"),
        help_text=_("Overall discount rate applied to the purchase."),
    )
    total_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Total Discount Amount"),
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Tax Rate (%)"),
    )
    total_tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Total Tax Amount"),
    )
    sub_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Subtotal"),
    )
    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Grand Total"),
    )
    supplier = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="inventory_purchases",
        verbose_name=_("Supplier"),
        help_text=_("Supplier from whom the purchase was made."),
        db_index=True,
    )
    bill_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Bill Number"),
    )
    bill_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Bill Date"),
    )
    due_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Due Date"),
    )
    ref_purchase_main = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("Reference Purchase"),
        help_text=_(
            "Reference to the original purchase in case of returns or corrections.",
        ),
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Remarks"),
    )

    class Meta:
        verbose_name = _("Purchase")
        verbose_name_plural = _("Purchases")
        ordering = ["-id", "created_date_ad"]

    def __str__(self):
        return f"{self.purchase_no_full}"


class InvPurchaseDetail(AbstractInfoModel):
    """Item-wise details of a purchase."""

    purchase_main = models.ForeignKey(
        InvPurchaseMain,
        on_delete=models.PROTECT,
        related_name="details",
        verbose_name=_("Purchase Main"),
    )
    item_category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="purchase_details",
        verbose_name=_("Item Category"),
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name="purchase_details",
        verbose_name=_("Item"),
    )
    purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Purchase Cost"),
    )
    min_sale_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Minimum Sale Price"),
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Quantity"),
    )
    is_taxable = models.BooleanField(
        default=True,
        verbose_name=_("Is Taxable"),
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name=_("Tax Rate (%)"),
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Tax Amount"),
    )
    is_discountable = models.BooleanField(
        default=True,
        verbose_name=_("Is Discountable"),
    )
    discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Discount Rate (%)"),
    )
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Discount Amount"),
    )
    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Gross Amount"),
    )
    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Net Amount"),
    )
    ref_purchase_detail = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("Reference Detail"),
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Remarks"),
    )

    class Meta:
        verbose_name = _("Purchase Detail")
        verbose_name_plural = _("Purchase Details")

    def __str__(self):
        return f"{self.item.name}"


class InvPurchasePaymentDetail(AbstractInfoModel):
    """Payment information linked to a purchase."""

    purchase_main = models.ForeignKey(
        InvPurchaseMain,
        on_delete=models.PROTECT,
        related_name="payments",
        verbose_name=_("Purchase Main"),
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        verbose_name=_("Payment Method"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Payment Amount"),
    )
    remarks = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Remarks"),
    )

    class Meta:
        verbose_name = _("Purchase Payment Detail")
        verbose_name_plural = _("Purchase Payment Details")

    def __str__(self):
        return f"Payment {self.id}"


class InvPurchaseAdditionalCharge(AbstractInfoModel):
    """Additional charges related to a purchase."""

    charge_type = models.ForeignKey(
        AdditionalChargeType,
        on_delete=models.PROTECT,
        verbose_name=_("Charge Type"),
    )
    purchase_main = models.ForeignKey(
        InvPurchaseMain,
        on_delete=models.PROTECT,
        related_name="charges",
        verbose_name=_("Purchase Main"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Charge Amount"),
    )
    remarks = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Remarks"),
    )

    class Meta:
        verbose_name = _("Additional Charge")
        verbose_name_plural = _("Additional Charges")

    def __str__(self):
        return f"Charge {self.id} - {self.charge_type.name}"


class InvPurchaseAttachment(AbstractInfoModel):
    """Attachments related to the purchase, such as bills or invoices."""

    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Attachment Title"),
    )
    purchase_main = models.ForeignKey(
        InvPurchaseMain,
        on_delete=models.PROTECT,
        related_name="attachments",
        verbose_name=_("Purchase Main"),
    )
    attachment = models.FileField(
        validators=[validate_file_extension],
        verbose_name=_("Attachment File"),
    )

    class Meta:
        verbose_name = _("Purchase Attachment")
        verbose_name_plural = _("Purchase Attachments")

    def __str__(self):
        return self.title or f"Attachment {self.id}"
