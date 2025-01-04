from django.contrib import admin

from .models import EmailConfig, OrganizationSetup, ThirdPartyCredential

admin.site.register(OrganizationSetup)
admin.site.register(ThirdPartyCredential)
admin.site.register(EmailConfig)
