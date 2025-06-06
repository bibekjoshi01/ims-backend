from django.contrib import admin

from .models import Purchase, SupplierPayment

admin.site.register(Purchase)
admin.site.register(SupplierPayment)
