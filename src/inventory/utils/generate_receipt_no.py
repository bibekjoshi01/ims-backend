from src.inventory.inv_credit_clearance.models import InvCreditClearanceMain
from src.custom_lib.functions.fiscal_session import (
    get_current_fiscal_year_code_ad,
    get_current_fiscal_year_code_bs,
)


# RECEIPT_NO_LENGTH according to given digits
RECEIPT_NO_LENGTH = 5
fiscal_year_code_bs = get_current_fiscal_year_code_bs()
fiscal_year_code_ad = get_current_fiscal_year_code_ad()


# generate unique order_no for receipt master
def get_unique_receipt_no(payment_type):
    # general calculations/settings/format
    receipt_no_detail = {}
    count = InvCreditClearanceMain.objects.filter(
        payment_type=payment_type, receipt_no__icontains=fiscal_year_code_bs
    ).count()
    max_id = str(count + 1)
    receipt_no = max_id.zfill(RECEIPT_NO_LENGTH)

    # for Purchase /Direct Purchase
    if payment_type == "PAYMENT":
        unique_id = "PRT-" + fiscal_year_code_bs + "-" + receipt_no
        receipt_no_detail["prefix"] = "PRT"  # Payment Receipt
        receipt_no_detail["separator"] = "-"
        receipt_no_detail["fiscal"] = fiscal_year_code_bs
        receipt_no_detail["receipt_no"] = receipt_no
        receipt_no_detail["receipt_no_full"] = unique_id
        return receipt_no_detail

    # for Purchase Returned
    elif payment_type == "RETURN":
        unique_id = "PRR-" + fiscal_year_code_bs + "-" + receipt_no
        receipt_no_detail["prefix"] = "PRR"  # Payment Receipt Return
        receipt_no_detail["separator"] = "-"
        receipt_no_detail["fiscal"] = fiscal_year_code_bs
        receipt_no_detail["receipt_no"] = receipt_no
        receipt_no_detail["receipt_no_full"] = unique_id

    else:
        return Exception("Invalid payment (receipt) type! Contact system vendor.")

    return receipt_no_detail
