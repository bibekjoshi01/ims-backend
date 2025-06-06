# Django Imports
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from src.base.models import AbstractInfoModel

# Project Imports
from src.core.models import AdditionalChargeType, PaymentMethod
from src.inventory.catalog.models import Product
from src.inventory.store.models import Store
from src.libs.validators import validate_file_extension
from src.supplier.models import Supplier

from .constants import PartyPaymentType, PayType, PurchaseType


class Purchase(AbstractInfoModel):
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
    prefix = models.CharField(max_length=3, help_text=_("Prefix like: PU"))
    purchase_no = models.PositiveIntegerField(
        verbose_name=_("Purchase Number"),
        help_text=_("Sequential number for tracking the purchase."),
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
    round_off_grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Round Off Amount"),
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="supplier_purchases",
        verbose_name=_("Supplier"),
        help_text=_("Supplier from whom the purchase was made."),
        db_index=True,
    )
    store = models.ForeignKey(
        Store,
        on_delete=models.SET_NULL,
        null=True,
        related_name="store_purchases",
        verbose_name=_("Store"),
        help_text=_("Store where purchase is stored or received."),
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
        help_text=_("Due date to pay if purchase is in credit."),
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
    notes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Notes"),
    )
    show_notes_on_invoice = models.BooleanField(
        default=False,
        help_text=_("Decides whether to show notes on invoice print."),
    )

    class Meta:
        verbose_name = _("Purchase")
        verbose_name_plural = _("Purchases")
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.purchase_no_full}"

    @property
    def purchase_no_full(self):
        """A complete identifier including prefixes or codes."""

        return f"{self.prefix}-{self.purchase_no}"


class PurchaseDetail(AbstractInfoModel):
    """Payment information linked to a purchase."""

    purchase_main = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        related_name="details",
        verbose_name=_("Purchase Main"),
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_details",
        verbose_name=_("Product"),
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_("Quantity"),
    )
    purchase_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Purchase Cost"),
    )
    min_sale_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Minimum Selling Price"),
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

    batch_no = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Batch Number"),
        help_text=_("Batch number for tracking purposes."),
    )
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Expiry Date"),
        help_text=_("Expiry date for the product, if applicable."),
    )
    track_serial = models.BooleanField(
        default=False,
        verbose_name=_("Track Serial/IMEI"),
    )

    ref_purchase_detail = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("Reference Purchase Detail"),
    )
    remarks = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Remarks"),
    )

    class Meta:
        verbose_name = _("Purchase Detail")
        verbose_name_plural = _("Purchase Details")
        ordering = ["-id"]

    def __str__(self) -> str:
        return f"{self.product.name}"


class PurchasePaymentDetail(AbstractInfoModel):
    """Payment information linked to a purchase."""

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        related_name="payment_details",
        verbose_name=_("Purchase"),
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

    def __str__(self) -> str:
        return f"Payment {self.id} - {self.payment_method.name}"


class PurchaseAdditionalCharge(AbstractInfoModel):
    """Additional charges related to a purchase."""

    charge_type = models.ForeignKey(
        AdditionalChargeType,
        on_delete=models.PROTECT,
        verbose_name=_("Charge Type"),
    )
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        related_name="additional_charges",
        verbose_name=_("Purchase"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Charge Amount"),
    )
    payment_date = models.DateField(
        verbose_name=_("Payment Date"),
        null=True,
        help_text=_("Date when this payment was done."),
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


class PurchaseAttachment(AbstractInfoModel):
    """Attachments related to the purchase, such as bills or invoices."""

    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Attachment Title"),
    )
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.PROTECT,
        related_name="attachments",
        verbose_name=_("Purchase"),
    )
    attachment = models.FileField(
        validators=[validate_file_extension],
        verbose_name=_("Attachment File"),
    )

    class Meta:
        verbose_name = _("Purchase Attachment")
        verbose_name_plural = _("Purchase Attachments")

    def __str__(self) -> str:
        return self.title or f"Attachment {self.id}"


class PurchaseDetailSerialNumber(AbstractInfoModel):
    """Serial Nos for purchase details products to keep unit wise tracking"""

    purchase_detail = models.ForeignKey(
        PurchaseDetail,
        on_delete=models.CASCADE,
        related_name="serial_numbers",
        verbose_name=_("Purchase Detail"),
    )
    serial_no = models.CharField(_("Serial Number"), max_length=255)
    ref_purchase_detail_serial_no = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
    )

    class Meta:
        verbose_name = _("Purchase Detail Serial Number")
        verbose_name_plural = _("Purchase Detail Serial Numbers")
        unique_together = ("serial_no", "purchase_detail")

    def __str__(self) -> str:
        return f"{self.id}"


class SupplierPayment(AbstractInfoModel):
    """
    Records a payment made to a supplier.
    """

    payment_type = models.CharField(
        choices=PartyPaymentType.choices(),
        max_length=20,
        verbose_name=_("Payment Type"),
        help_text=_("Type of payment, e.g., payment, return"),
    )
    payment_no = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Payment Number"),
        help_text=_("System-generated"),
    )
    receipt_no = models.CharField(
        max_length=20,
        verbose_name=_("Receipt Number"),
        help_text=_("Receipt number provided to the supplier, Reference Number"),
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        verbose_name=_("Supplier"),
        help_text=_("The supplier to whom the payment was made"),
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Total Amount Paid"),
        help_text=_("Total payment amount made to the supplier"),
    )
    payment_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Payment Date"),
        help_text=_("Date on which payment was made"),
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Any additional information or remarks about this payment"),
    )

    class Meta:
        verbose_name = _("Supplier Payment")
        verbose_name_plural = _("Supplier Payments")
        ordering = ["-payment_date"]

    def __str__(self):
        return f"#{self.payment_no or self.id} {_('to')} {self.supplier.name}"


class SupplierPaymentDetail(AbstractInfoModel):
    """
    Records individual payment method details for a supplier payment.
    """

    supplier_payment = models.ForeignKey(
        SupplierPayment,
        on_delete=models.PROTECT,
        related_name="details",
        verbose_name=_("Supplier Payment"),
        help_text=_("The main payment record this detail belongs to"),
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        verbose_name=_("Payment Method"),
        help_text=_("Method used for the payment (e.g., cash, bank transfer)"),
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_("Amount"),
        help_text=_("Amount paid using this method"),
    )
    remarks = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Remarks"),
        help_text=_("Optional remarks about this payment method"),
    )

    class Meta:
        verbose_name = _("Supplier Payment Detail")
        verbose_name_plural = _("Supplier Payment Details")

    def __str__(self):
        return f"{self.amount} {_('via')} {self.payment_method} ({_('Payment')})"
