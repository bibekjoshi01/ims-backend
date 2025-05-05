from django.dispatch import receiver
from django.db.models import signals
from rest_framework.serializers import ValidationError
from .models import InvPurchaseDetail
from src.inventory.inv_stock.models import ProductWiseStock, PurchaseWiseStock


"""
    Tracks new purchase and signals to
    update the stock
"""


@receiver(signals.post_save, sender=InvPurchaseDetail)
def new_purchase_signal(sender, instance, created, **kwargs):
    if created:
        try:
            # New purchase or purchase return is created
            purchase_type = instance.purchase_main.purchase_type

            # Update the corresponding stock model based on the purchase type
            if purchase_type == "PURCHASE":
                # Update ProductWiseStock for new purchase
                product_stock, created = ProductWiseStock.objects.get_or_create(
                    product_variant=instance.product_variant,
                )
                product_stock.update_stock_quantities(purchase_qty=instance.qty)
                product_stock.save()

                # Update PurchaseWiseStock for purchase
                purchase_stock, created = PurchaseWiseStock.objects.get_or_create(
                    purchase=instance,
                )
                purchase_stock.update_stock_quantities(purchase_qty=instance.qty)
                purchase_stock.save()

            elif purchase_type == "RETURN":
                # Update ProductWiseStock for purchase return
                product_stock, created = ProductWiseStock.objects.get_or_create(
                    product_variant=instance.product_variant
                )
                product_stock.update_stock_quantities(purchase_return_qty=instance.qty)
                product_stock.save()

                # Update PurchaseWiseStock for purchase return
                purchase_stock, created = PurchaseWiseStock.objects.get_or_create(
                    purchase=instance,
                )
                purchase_stock.update_stock_quantities(purchase_return_qty=instance.qty)
                purchase_stock.save()

        except Exception as e:
            raise ValidationError({"signals": str(e)})
