from django.apps import AppConfig


class InvPurchaseConfig(AppConfig):
    name = "src.inventory.inv_purchase"

    def ready(self):
        import src.inventory.purchase.signals
