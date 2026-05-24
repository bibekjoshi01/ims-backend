from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from .models import Tenant
from .serializers import TenantListSerializer


class TenantListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TenantListSerializer
    queryset = Tenant.objects.all()
