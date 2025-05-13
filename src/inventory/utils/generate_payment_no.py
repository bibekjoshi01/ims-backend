from src.inventory.inv_party_payment.models import InvPartyPayment
from rest_framework import serializers
from src.core_app.models import FiscalSessionAD
from src.custom_lib.functions.fiscal_session import (
    get_full_fiscal_year_code_bs,
    get_current_fiscal_year_code_ad,
)


PURCHASE_ORDER_LENGTH = 5


def get_inv_payment_no(payment_type):
    try:
        fiscal_session_ad = FiscalSessionAD.objects.get(
            session_short=get_current_fiscal_year_code_ad()
        )
    except Exception as e:
        raise serializers.ValidationError(
            "Invalid fiscal session. Session Ids do not match."
        )

    count = InvPartyPayment.objects.filter(
        payment_type=payment_type, fiscal_session_ad=fiscal_session_ad
    ).count()
    max_id = str(count + 1)
    fiscal_year_code = get_full_fiscal_year_code_bs()
    fy_start = fiscal_year_code[2:4]  # extract first two characters
    fy_end = fiscal_year_code[-2:]  # extract last two characters
    fiscal_year_code = fy_start + "/" + fy_end  # combine the two extracted parts
    if payment_type == "PAYMENT":
        payment_no = (
            "PPP-" + fiscal_year_code + "-" + max_id.zfill(PURCHASE_ORDER_LENGTH)
        )
    else:
        payment_no = (
            "PPR-" + fiscal_year_code + "-" + max_id.zfill(PURCHASE_ORDER_LENGTH)
        )
    return payment_no
