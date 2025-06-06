from rest_framework import serializers

# Project Imports
from src.core.models import AdditionalChargeType, PaymentMethod
from src.inventory.catalog.models import Product
from src.supplier.models import Supplier
from .models import (
    Purchase,
    PurchaseDetail,
    PurchaseAttachment,
    PurchaseAdditionalCharge,
    PurchaseDetailSerialNumber,
    PurchasePaymentDetail,
)

# --------------------------------------------------------------------------------------------
# List Serializers
# --------------------------------------------------------------------------------------------


class SupplierForPurchaseListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "email", "contact_person" "phone_no", "phone_no_alt"]


class PurchaseListSerializer(serializers.ModelSerializer):
    pay_type_display = serializers.CharField(source="get_pay_type_display")
    purchase_no_full = serializers.CharField(source="purchase_no_full")
    supplier = SupplierForPurchaseListSerializer()

    class Meta:
        model = Purchase
        fieldss = [
            "id",
            "purchase_no",
            "pay_type",
            "pay_type_display",
            "purchase_no_full",
            "pay_type",
            "discount_rate",
            "total_discount_amount",
            "tax_rate",
            "total_tax_amount",
            "sub_total",
            "grand_total",
            "round_off_grand_total",
            "supplier",
            "bill_no",
            "bill_date",
            "due_date",
        ]


# --------------------------------------------------------------------------------------------
# Retrieve Serializers
# --------------------------------------------------------------------------------------------


class PurchaseDetailSerialNumberRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseDetailSerialNumber
        fields = ["id", "serial_no"]


class PurchaseAttachmentRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseAttachment
        fields = ["id", "title", "attachment"]


class PurchaseAdditionalChargeRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchaseAdditionalCharge
        fields = ["id", "charge_type", "amount", "payment_date", "remarks"]


class PurchasePaymentDetailRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = PurchasePaymentDetail
        fields = ["id", "payment_method", "amount", "remarks"]


class PurchaseDetailRetrieveSerializer(serializers.ModelSerializer):
    serial_numbers = PurchaseDetailSerialNumberRetrieveSerializer(many=True)

    class Meta:
        model = PurchaseDetail
        fields = [
            "id",
            "product",
            "quantity",
            "purchase_cost",
            "min_sale_cost",
            "tax_rate",
            "tax_amount",
            "discount_rate",
            "discount_amount",
            "tax_rate",
            "tax_amount",
            "gross_amount",
            "net_amount",
            "batch_no",
            "expiry_date",
            "track_serial",
            "remarks",
            "serial_numbers",
        ]


class PurchaseRetrieveSerializer(serializers.ModelSerializer):

    details = PurchaseDetailRetrieveSerializer(many=True)
    payment_details = PurchasePaymentDetailRetrieveSerializer(many=True)
    additional_charges = PurchaseAdditionalChargeRetrieveSerializer(many=True)
    attachments = PurchaseAttachmentRetrieveSerializer(many=True)
    supplier = SupplierForPurchaseListSerializer()
    pay_type_display = serializers.CharField(source="get_pay_type_display")

    class Meta:
        model = Purchase
        fieldss = [
            "id",
            "pay_type",
            "pay_type_display",
            "purchase_no",
            "purchase_no_full",
            "discount_rate",
            "total_discount_amount",
            "tax_rate",
            "total_tax_amount",
            "sub_total",
            "grand_total",
            "round_off_grand_total",
            "supplier",
            "bill_no",
            "bill_date",
            "due_date",
            "notes",
            "show_notes_on_invoice",
            # Nested
            "details",
            "payment_details",
            "additional_charges",
            "attachments",
        ]


# --------------------------------------------------------------------------------------------
# Create Serializers
# --------------------------------------------------------------------------------------------


class PurchaseDetailSerialNumberCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseDetailSerialNumber
        fields = ["serial_no"]


class PurchaseAttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseAttachment
        fields = ["title", "attachment"]


class PurchaseAdditionalChargeCreateSerializer(serializers.ModelSerializer):
    charge_type = serializers.PrimaryKeyRelatedField(
        queryset=AdditionalChargeType.objects.filter(is_active=True)
    )

    class Meta:
        model = PurchaseAdditionalCharge
        fields = ["charge_type", "amount", "payment_date", "remarks"]


class PurchasePaymentDetailCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.filter(is_active=True)
    )

    class Meta:
        model = PurchasePaymentDetail
        fields = ["payment_method", "amount", "remarks"]


class PurchaseDetailCreateSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True)
    )
    serial_numbers = PurchaseDetailSerialNumberCreateSerializer(many=True)

    class Meta:
        model = PurchaseDetail
        fields = [
            "product",
            "quantity",
            "purchase_cost",
            "min_sale_cost",
            "tax_rate",
            "tax_amount",
            "discount_rate",
            "discount_amount",
            "tax_rate",
            "tax_amount",
            "gross_amount",
            "net_amount",
            "batch_no",
            "expiry_date",
            "track_serial",
            "remarks",
            "serial_numbers",
        ]


class PurchaseCreateSerializer(serializers.ModelSerializer):

    details = PurchaseDetailCreateSerializer(many=True)
    payment_details = PurchasePaymentDetailCreateSerializer(many=True)
    additional_charges = PurchaseAdditionalChargeCreateSerializer(many=True)
    attachments = PurchaseAttachmentCreateSerializer(many=True)

    supplier = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.filter(is_active=True)
    )

    class Meta:
        model = Purchase
        fieldss = [
            "pay_type",
            "discount_rate",
            "total_discount_amount",
            "tax_rate",
            "total_tax_amount",
            "sub_total",
            "grand_total",
            "round_off_grand_total",
            "supplier",
            "bill_no",
            "bill_date",
            "due_date",
            "notes",
            "show_notes_on_invoice",
            # Nested
            "details",
            "payment_details",
            "additional_charges",
            "attachments",
        ]
