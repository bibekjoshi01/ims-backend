from src.base.constants import BaseEnum


class PurchaseType(BaseEnum):
    PURCHASE = "PURCHASE"
    RETURN = "RETURN"


class PayType(BaseEnum):
    CASH = "CASH"
    CREDIT = "CREDIT"


class PartyPaymentType(BaseEnum):
    PAYMENT = "PAYMENT"
    RETURN = "RETURN"
