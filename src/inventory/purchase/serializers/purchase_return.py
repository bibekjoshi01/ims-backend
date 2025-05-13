from decimal import Decimal
from rest_framework import serializers

from src.inventory.utils.generate_purchase_no import generate_unique_purchase_number
from src.inventory.utils.validators import (
    validate_amount,
    validate_percentage,
)
from src.inventory.purchase.models import (
    InvPurchaseAdditionalCharge,
    InvPurchasePaymentDetail,
    InvPurchaseDetail,
    InvPurchaseMain,
)
from .common import (
    InvPurchaseDetailCreateSerializer,
    InvPurchaseAdditionalChargeCreateSerializer,
    InvPurchaseAttachmentCreateSerializer,
    InvPurchasePaymentDetailCreateSerializer,
)


class InvPurchaseDetailCreateSerializerForPurchaseReturn(
    InvPurchaseDetailCreateSerializer
):
    ref_purchase_detail = serializers.PrimaryKeyRelatedField(
        queryset=InvPurchaseDetail.objects.filter(
            purchase_main__purchase_type="PURCHASE", ref_purchase_detail__isnull=True
        ),
    )

    class Meta(InvPurchaseDetailCreateSerializer.Meta):
        fields = InvPurchaseDetailCreateSerializer.Meta.fields + ["ref_purchase_detail"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude product_variant and product_category from the serializer's fields
        self.fields.pop("product_variant", None)
        self.fields.pop("product_category", None)


class InvPurchaseReturnCreateSerializer(serializers.ModelSerializer):
    remarks = serializers.CharField(max_length=150)
    ref_purchase_main = serializers.PrimaryKeyRelatedField(
        queryset=InvPurchaseMain.objects.filter(
            purchase_type="PURCHASE", ref_purchase_main__isnull=True
        ),
    )

    tax_rate = serializers.IntegerField(validators=[validate_percentage])
    discount_rate = serializers.IntegerField(validators=[validate_percentage])
    total_discount = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    total_tax = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    sub_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )
    grand_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, validators=[validate_amount]
    )

    purchase_details = InvPurchaseDetailCreateSerializerForPurchaseReturn(many=True)
    payment_details = InvPurchasePaymentDetailCreateSerializer(many=True)
    additional_charges = InvPurchaseAdditionalChargeCreateSerializer(
        many=True, allow_null=True
    )
    attachments = InvPurchaseAttachmentCreateSerializer(many=True, allow_null=True)

    class Meta:
        model = InvPurchaseMain
        fields = [
            "pay_type",
            "discount_rate",
            "total_discount",
            "tax_rate",
            "total_tax",
            "sub_total",
            "grand_total",
            "remarks",
            "ref_purchase_main",
        ] + ["purchase_details", "payment_details", "additional_charges", "attachments"]

    def validate_payment_details(self, payment_details):
        validated_data = self.initial_data
        total_payment = Decimal("0.00")
        quantize_places = Decimal(10) ** -2

        for payment_detail in payment_details:
            total_payment += Decimal(payment_detail["amount"])

        grand_total = Decimal(validated_data["grand_total"])

        if validated_data["pay_type"] == "CASH":
            if total_payment.quantize(quantize_places) != grand_total.quantize(
                quantize_places
            ):
                raise serializers.ValidationError(
                    {
                        "amount": "Sum of amount {} should be equal to grand_total {} in pay_type CASH.".format(
                            total_payment, grand_total
                        )
                    }
                )
        elif validated_data["pay_type"] == "CREDIT":
            if total_payment > grand_total:
                raise serializers.ValidationError(
                    {
                        "amount": "Cannot process purchase CREDIT with total paid amount greater than {}".format(
                            grand_total
                        )
                    }
                )

        return payment_details

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        quantize_places = Decimal(10) ** -2

        sub_total = Decimal("0.00")
        total_discount = Decimal("0.00")
        total_tax = Decimal("0.00")
        total_discountable_amount = Decimal("0.00")
        total_taxable_amount = Decimal("0.00")
        total_nontaxable_amount = Decimal("0.00")
        partial_taxable_amount = Decimal("0.00")

        purchase_details = validated_data.get("purchase_details")

        for purchase_detail in purchase_details:
            calculated_net_amount = Decimal("0.00")
            calculated_discount_amount = Decimal("0.00")
            calculated_tax_amount = Decimal("0.00")

            # Validating gross amount
            calculated_gross_amount = (
                purchase_detail["purchase_cost"] * purchase_detail["qty"]
            )
            if purchase_detail["gross_amount"] != calculated_gross_amount.quantize(
                quantize_places
            ):
                raise serializers.ValidationError(
                    {
                        "gross_amount": f"Invalid gross amount: should be {calculated_gross_amount}"
                    }
                )

            sub_total += calculated_gross_amount

            # Validating discount amount
            if purchase_detail["discountable"]:
                total_discountable_amount += purchase_detail["gross_amount"]

                if (
                    purchase_detail["discount_rate"] <= 0
                    or purchase_detail["discount_amount"] <= 0
                ):
                    raise serializers.ValidationError(
                        {"discount": "Invalid Discount !"}
                    )

                calculated_discount_amount = (
                    purchase_detail["discount_rate"] * purchase_detail["gross_amount"]
                ) / Decimal("100")
                if calculated_discount_amount != purchase_detail["discount_amount"]:
                    raise serializers.ValidationError(
                        {
                            f"discount_amount": f"Invalid discount amount: should be {calculated_discount_amount}"
                        }
                    )

                total_discount += purchase_detail["discount_amount"]
            else:
                if (
                    purchase_detail["discount_rate"] > 0
                    or purchase_detail["discount_amount"] > 0
                ):
                    raise serializers.ValidationError(
                        {
                            "discount": f"Invalid discount rate or discount amount for non discountable product."
                        }
                    )

            # validating tax amount
            partial_taxable_amount = (
                purchase_detail["gross_amount"] - purchase_detail["discount_amount"]
            )

            if purchase_detail["taxable"]:
                total_taxable_amount += partial_taxable_amount

                if (
                    purchase_detail["tax_rate"] <= 0
                    and purchase_detail["tax_amount"] <= 0
                ):
                    raise serializers.ValidationError({"tax": "Invalid Tax !"})

                calculated_tax_amount = (
                    purchase_detail["tax_rate"]
                    * (calculated_gross_amount - calculated_discount_amount)
                ) / Decimal("100")

                if calculated_tax_amount != purchase_detail["tax_amount"]:
                    raise serializers.ValidationError(
                        {
                            f"tax_amount": f"Invalid tax amount: should be {calculated_tax_amount}"
                        }
                    )

                total_tax += purchase_detail["tax_amount"]
            else:
                if purchase_detail["tax_rate"] > 0 or purchase_detail["tax_amount"] > 0:
                    raise serializers.ValidationError(
                        {
                            "discount": "Invalid tax rate or tax amount for non-taxable product."
                        }
                    )

                total_nontaxable_amount += partial_taxable_amount

            # Validating net amount
            calculated_net_amount = (
                purchase_detail["gross_amount"]
                - purchase_detail["discount_amount"]
                + purchase_detail["tax_amount"]
            )
            if calculated_net_amount != purchase_detail["net_amount"]:
                raise serializers.ValidationError(
                    {
                        "net_amount": f"Invalid net amount: should be {calculated_net_amount}"
                    }
                )

        # Validating total discount
        calculated_total_discount_amount = (
            Decimal(total_discountable_amount * validated_data["discount_rate"])
            / Decimal("100.00")
        ).quantize(quantize_places)

        if calculated_total_discount_amount != total_discount:
            raise serializers.ValidationError(
                "discount_rate got {} invalid value !".format(
                    validated_data["discount_rate"]
                )
            )

        if any(
            value != validated_data["total_discount"]
            for value in [calculated_total_discount_amount, total_discount]
        ):
            raise serializers.ValidationError(
                "total_discount got {} not valid: expected {}".format(
                    validated_data["total_discount"], total_discount
                )
            )

        # Validating total total tax
        calculated_total_tax_amount = (
            Decimal(total_taxable_amount * validated_data["tax_rate"])
            / Decimal("100.00")
        ).quantize(quantize_places)

        if calculated_total_tax_amount != total_tax:
            raise serializers.ValidationError(
                "tax_rate got {} invalid value !".format(validated_data["tax_rate"])
            )

        if any(
            value != validated_data["total_tax"]
            for value in [calculated_total_tax_amount, total_tax]
        ):
            raise serializers.ValidationError(
                "total_tax got {} not valid: expected {}".format(
                    validated_data["total_tax"], total_tax
                )
            )

        # Validating sub_total amount
        if sub_total != validated_data["sub_total"]:
            raise serializers.ValidationError(
                "sub_total calculation not valid: should be {}".format(sub_total)
            )

        # Validating grand total amount
        additional_charges = attrs["additional_charges"]

        total_additional_charge = Decimal("0.00")
        total_amount = Decimal("0.00")
        calculated_grand_total = Decimal("0.00")

        if additional_charges is not None:
            for charge in additional_charges:
                total_additional_charge += charge["amount"]

        for purchase_detail in purchase_details:
            total_amount += purchase_detail["net_amount"]

        calculated_grand_total = total_amount + total_additional_charge

        if calculated_grand_total.quantize(quantize_places) != attrs["grand_total"]:
            raise serializers.ValidationError(
                {
                    "grand_total": f"Invalid grand total: should be {calculated_grand_total}"
                }
            )

        return attrs

    def create(self, validated_data):
        purchase_details = validated_data.pop("purchase_details")
        payment_details = validated_data.pop("payment_details")
        additional_charges = validated_data.pop("additional_charges", None)
        attachments = validated_data.pop("attachments", None)

        purchase_no_detail = generate_unique_purchase_number(purchase_type="RETURN")
        current_fiscal_session_detail = get_current_fiscal_session_detail()
        current_timestamp_and_user_detail = get_current_time_stamp_and_user_for_db_op(
            self.context
        )

        validated_data["purchase_type"] = "RETURN"
        ref_purchase_main = validated_data["ref_purchase_main"]

        # set bill date
        validated_data["bill_date_bs"] = ref_purchase_main.bill_date_bs
        validated_data["bill_date_ad"] = ref_purchase_main.bill_date_ad

        # set bill's due date
        validated_data["due_date_bs"] = ref_purchase_main.due_date_bs
        validated_data["due_date_ad"] = ref_purchase_main.due_date_ad
        validated_data["supplier"] = ref_purchase_main.supplier
        validated_data["bill_no"] = ref_purchase_main.bill_no

        # Creating Purchase Main Instance
        purchase_main_instance = InvPurchaseMain.objects.create(
            **validated_data,
            **purchase_no_detail,
            **current_fiscal_session_detail,
            **current_timestamp_and_user_detail,
        )

        # Creating Purchase Details for Purchase
        for purchase_detail in purchase_details:
            # setting the product and product_category
            purchase_detail["product_variant"] = purchase_detail[
                "ref_purchase_detail"
            ].product_variant
            purchase_detail["product_category"] = purchase_detail[
                "ref_purchase_detail"
            ].product_category

            InvPurchaseDetail.objects.create(
                purchase_main=purchase_main_instance,
                **purchase_detail,
                **current_timestamp_and_user_detail,
            )

        # Creating Payment Details for Purchase
        for payment_detail in payment_details:
            InvPurchasePaymentDetail.objects.create(
                purchase_main=purchase_main_instance,
                **payment_detail,
                **current_timestamp_and_user_detail,
            )

        # Creating Additional Charges for Purchase
        if additional_charges is not None:
            for additional_charge in additional_charges:
                InvPurchaseAdditionalCharge.objects.create(
                    purchase_main=purchase_main_instance,
                    **additional_charge,
                    **current_timestamp_and_user_detail,
                )

        # Creating Additional Charges for Purchase
        if attachments is not None:
            for attachment in attachments:
                InvPurchaseAdditionalCharge.objects.create(
                    purchase_main=purchase_main_instance,
                    **attachment,
                    **current_timestamp_and_user_detail,
                )

        return purchase_main_instance
