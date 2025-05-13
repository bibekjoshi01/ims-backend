from src.inventory.inv_sale.models import InvSaleMain
from src.core_app.models import FiscalSessionBS
from rest_framework import serializers
from src.custom_lib.functions.fiscal_session import (
    get_current_fiscal_year_code_ad,
    get_current_fiscal_year_code_bs,
)

# format order_no according to given digits
SALE_NO_LENGTH = 6
current_fiscal_year_code_bs = get_current_fiscal_year_code_bs()
current_fiscal_year_code_ad = get_current_fiscal_year_code_ad()


# generate unique order_no for sale main
def generate_sale_no_detail(sale_type):
    # Process fiscal session related information
    try:
        fiscal_session_bs = FiscalSessionBS.objects.get(
            session_short=current_fiscal_year_code_bs
        )
    except Exception as e:
        raise serializers.ValidationError(
            "Invalid fiscal session. Session Ids do not match."
        )
    sale_no_detail = {}
    count = InvSaleMain.objects.filter(
        sale_type=sale_type, fiscal_session_bs=fiscal_session_bs
    ).count()
    max_id = str(count + 1)
    sale_no = max_id.zfill(SALE_NO_LENGTH)

    # for direct sale
    if sale_type == "SALE":
        unique_id = "SA-" + current_fiscal_year_code_bs + "-" + sale_no
        sale_no_detail["sale_no"] = sale_no
        sale_no_detail["sale_no_full"] = unique_id
        return sale_no_detail

    # for sale Returned
    elif sale_type == "RETURN":
        unique_id = "SR-" + current_fiscal_year_code_bs + "-" + sale_no
        sale_no_detail["sale_no"] = sale_no
        sale_no_detail["sale_no_full"] = unique_id

    else:
        return Exception("Invalid sale type! Contact system vendor.")

    return sale_no_detail
