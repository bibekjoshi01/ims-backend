from django.contrib import admin

from .models import Customer, CustomerAddress

admin.site.register(Customer)
admin.site.register(CustomerAddress)
