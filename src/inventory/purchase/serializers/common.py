from rest_framework import serializers

# Project Imports
from src.base.serializers import AbstractInfoRetrieveSerializer
from src.core.models import AdditionalChargeType, PaymentMethod
from src.inventory.catalog.models import Item, ItemCategory
from src.inventory.utils.validators import (
    validate_amount,
    validate_percentage,
    validate_positive_integer,
)
from ..models import (
    InvPurchaseAdditionalCharge,
    InvPurchaseAttachment,
    InvPurchaseDetail,
    InvPurchaseMain,
    InvPurchasePaymentDetail,
)


# List Serializers


class InvPurchaseDetailListSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvPurchaseDetail
        fields = [
            "id",
            "product_category",
            "product_variant",
            "purchase_cost",
            "min_sale_cost",
            "qty",
            "taxable",
            "tax_rate",
            "tax_amount",
            "discountable",
            "discount_rate",
            "discount_amount",
            "gross_amount",
            "net_amount",
            "note",
            "ref_purchase_detail",
        ]


class InvPurchasePaymentDetailListSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvPurchasePaymentDetail
        fields = ["id", "payment_method", "amount", "remarks"]


class InvPurchaseAdditionalChargeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvPurchaseAdditionalCharge
        fields = ["id", "charge_type", "amount", "remarks"]


class InvPurchaseAttachmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvPurchaseAttachment
        fields = [
            "id",
            "title",
            "attachment",
        ]


class InvPurchaseListSerializer(serializers.ModelSerializer):
    supplier_full_name = serializers.ReadOnlyField(source="supplier.user.full_name")
    purchase_type = serializers.ReadOnlyField(source="get_purchase_type_display")
    pay_type = serializers.ReadOnlyField(source="get_pay_type_display")

    class Meta:
        model = InvPurchaseMain
        fields = [
            "id",
            "pay_type",
            "purchase_type",
            "purchase_no",
            "purchase_no_full",
            "supplier_full_name",
            "sub_total",
            "grand_total",
            "bill_no",
            "bill_date_ad",
            "bill_date_bs",
            "chalan_no",
            "total_discount",
            "total_tax",
            "due_date_ad",
            "due_date_bs",
            "remarks",
            "ref_purchase_main",
        ]


class InvPurchaseMainRetrieveSerializer(AbstractInfoRetrieveSerializer):
    supplier_full_name = serializers.ReadOnlyField(source="supplier.user.full_name")
    purchase_type = serializers.ReadOnlyField(source="get_purchase_type_display")
    pay_type = serializers.ReadOnlyField(source="get_pay_type_display")

    purchase_details = InvPurchaseDetailListSerializer(many=True)
    payment_details = InvPurchasePaymentDetailListSerializer(many=True)
    attachments = InvPurchaseAttachmentListSerializer(many=True, allow_null=True)
    additional_charges = InvPurchaseAdditionalChargeListSerializer(
        many=True, allow_null=True
    )

    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = InvPurchaseMain
        fields = [
            "id",
            "purchase_no_full",
            "purchase_type",
            "pay_type",
            "discount_rate",
            "total_discount",
            "tax_rate",
            "total_tax",
            "sub_total",
            "grand_total",
            "supplier_full_name",
            "bill_no",
            "bill_date_ad",
            "bill_date_bs",
            "chalan_no",
            "due_date_ad",
            "due_date_bs",
            "remarks",
            "ref_purchase_main",
        ] + ["purchase_details", "payment_details", "additional_charges", "attachments"]

        fields += AbstractInfoRetrieveSerializer.Meta.fields


# Create Serializers


class InvPurchaseDetailCreateSerializer(serializers.ModelSerializer):
    item_category = serializers.PrimaryKeyRelatedField(
        queryset=ItemCategory.objects.filter(is_active=True)
    )
    item = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.filter(is_active=True)
    )

    tax_rate = serializers.IntegerField(validators=[validate_percentage])
    discount_rate = serializers.IntegerField(validators=[validate_percentage])
    purchase_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    min_sale_cost = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    tax_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    gross_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    net_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    quantity = serializers.IntegerField(validators=[validate_positive_integer])

    class Meta:
        model = InvPurchaseDetail
        fields = [
            "product_category",
            "product_variant",
            "purchase_cost",
            "min_sale_cost",
            "quantity",
            "taxable",
            "tax_rate",
            "tax_amount",
            "discountable",
            "discount_rate",
            "discount_amount",
            "gross_amount",
            "net_amount",
            "remarks",
        ]


class InvPurchasePaymentDetailCreateSerializer(serializers.ModelSerializer):
    payment_method = serializers.PrimaryKeyRelatedField(
        queryset=PaymentMethod.objects.filter(is_active=True)
    )

    class Meta:
        model = InvPurchasePaymentDetail
        fields = ["payment_method", "amount", "remarks"]


class InvPurchaseAdditionalChargeCreateSerializer(serializers.ModelSerializer):
    charge_type = serializers.PrimaryKeyRelatedField(
        queryset=AdditionalChargeType.objects.filter(is_active=True)
    )

    class Meta:
        model = InvPurchaseAdditionalCharge
        fields = ["charge_type", "amount", "remarks"]


class InvPurchaseAttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvPurchaseAttachment
        fields = ["title", "attachment"]
