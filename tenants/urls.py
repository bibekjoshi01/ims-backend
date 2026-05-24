from django.urls import path

from tenants.views import TenantListAPIView

urlpatterns = [
    path("tenants", TenantListAPIView.as_view()),
]
