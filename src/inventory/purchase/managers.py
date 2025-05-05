from django.db import models


class InvPurchaseMainManager(models.Manager):
    def get_purchases_by_supplier(self, supplier):
        """
        Retrieve all purchases associated with a specific supplier.
        """
        return self.filter(supplier=supplier)

    def get_total_purchase_count(self):
        """
        Get the total count of purchases.
        """
        return self.count()

    def get_purchase_by_id(self, purchase_id):
        """
        Retrieve a purchase by its ID.
        """
        try:
            return self.get(id=purchase_id)
        except self.model.DoesNotExist:
            return None
