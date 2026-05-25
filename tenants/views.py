from rest_framework.generics import ListAPIView

# Project Imports
from control_plane.permissions import IsPlatformAdmin

from .models import Tenant
from .serializers import TenantListSerializer


class TenantListAPIView(ListAPIView):
    permission_classes = [IsPlatformAdmin]
    serializer_class = TenantListSerializer
    queryset = Tenant.objects.all()
