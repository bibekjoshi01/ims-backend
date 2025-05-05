from rest_framework import serializers

from src.core.models import AdditionalChargeType, PaymentMethod
from src.inventory.catalog.models import Item, ItemCategory
from src.inventory.purchase.models import InvPurchaseDetail, InvPurchaseMain
from src.inventory.supplier.models import InvSupplier


class ItemCategoryForPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCategory
        fields = ["id", "name"]


class ItemForPurchaseSerializer(serializers.ModelSerializer):
    category = serializers.IntegerField(source="product.category.id")

    class Meta:
        model = Item
        fields = ["id", "name", "category", "sku"]


class PaymentMethodForPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ["id", "name"]


class SupplierForPurchaseSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.first_name")
    email = serializers.CharField(source="user.email")
    mobile_no = serializers.CharField(source="user.mobile_no")

    class Meta:
        model = InvSupplier
        fields = ["id", "full_name", "email", "mobile_no"]


class AdditionalChargeTypeForPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalChargeType
        fields = ["id", "name"]


class PurchaseDetailForPurchaseSerializer(serializers.ModelSerializer):
    available_stock_qty = serializers.SerializerMethodField()

    class Meta:
        model = InvPurchaseDetail
        fields = [
            "id",
            "purchase_main",
            "product_variant",
            "purchase_cost",
            "min_sale_cost",
            "qty",
            "tax_rate",
            "tax_amount",
            "discountable",
            "discount_rate",
            "discount_amount",
            "gross_amount",
            "net_amount",
            "available_stock_qty",
        ]

    def get_available_stock_qty(self, obj):
        try:
            purchase_stock_instance = obj.purchase_wise_stock.get()
            available_stock_qty = purchase_stock_instance.available_stock_qty
        except PurchaseWiseStock.DoesNotExist:
            available_stock_qty = 0
        return available_stock_qty


class PurchaseForPurchaseReturnSerializer(serializers.ModelSerializer):
    purchase_type_display = serializers.ReadOnlyField(
        source="get_purchase_type_display"
    )
    pay_type_display = serializers.ReadOnlyField(source="get_pay_type_display")
    created_by_user_name = serializers.ReadOnlyField(source="created_by.user_name")
    created_by_full_name = serializers.ReadOnlyField(
        source="created_by.user.get_full_name"
    )

    class Meta:
        model = InvPurchaseMain
        fields = [
            "id",
            "supplier",
            "purchase_no_full",
            "purchase_type",
            "purchase_type_display",
            "pay_type",
            "pay_type_display",
            "sub_total",
            "discount_rate",
            "total_discount",
            "total_tax",
            "grand_total",
            "bill_no",
            "bill_date_ad",
            "bill_date_bs",
            "chalan_no",
            "due_date_ad",
            "due_date_bs",
            "remarks",
            "created_by_full_name",
            "created_by_user_name",
            "ref_purchase_main",
        ]
