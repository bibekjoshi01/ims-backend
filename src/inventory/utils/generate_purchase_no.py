from rest_framework import serializers

from src.core_app.models import FiscalSessionBS
from src.inventory.inv_purchase.models import InvPurchaseMain
from src.custom_lib.functions.fiscal_session import (
    get_current_fiscal_year_code_ad,
    get_current_fiscal_year_code_bs,
)

# Format order_no according to given digits
PURCHASE_ORDER_LENGTH = 4
PURCHASE_NO_LENGTH = 4

current_fiscal_year_code_bs = get_current_fiscal_year_code_bs()
current_fiscal_year_code_ad = get_current_fiscal_year_code_ad()


# Purchase Number Generator Function
def generate_unique_purchase_number(purchase_type):
    # Process fiscal session related information
    try:
        fiscal_session_bs = FiscalSessionBS.objects.get(
            session_short=current_fiscal_year_code_bs
        )
    except Exception as e:
        raise serializers.ValidationError(
            "Invalid fiscal session. Session Ids do not match.", str(e)
        )

    # general calculations/settings/format
    purchase_no_detail = {}
    count = InvPurchaseMain.objects.filter(fiscal_session_bs=fiscal_session_bs).count()

    max_id = str(count + 1)
    purchase_no = max_id.zfill(PURCHASE_NO_LENGTH)

    # for Purchase /Direct Purchase
    if purchase_type == "PURCHASE":
        unique_id = "PU-" + current_fiscal_year_code_bs + "-" + purchase_no
        purchase_no_detail["purchase_no"] = purchase_no
        purchase_no_detail["purchase_no_full"] = unique_id
        return purchase_no_detail

    # for Purchase Returned
    elif purchase_type == "RETURN":
        unique_id = "PR-" + current_fiscal_year_code_bs + "-" + purchase_no
        purchase_no_detail["purchase_no"] = purchase_no
        purchase_no_detail["purchase_no_full"] = unique_id
    else:
        return Exception("Invalid purhcase type! Contact system vendor.")

    return purchase_no_detail
