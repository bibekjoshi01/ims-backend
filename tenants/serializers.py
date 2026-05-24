from rest_framework import serializers

from .models import Tenant


class TenantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "subdomain"]
