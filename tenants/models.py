from django.db import models
from django.utils import timezone
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    """Core tenant isolation model."""

    name = models.CharField(max_length=200, unique=True)
    subdomain = models.SlugField(max_length=100, unique=True)

    is_active = models.BooleanField(default=True)

    # lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)

    # schema creation
    auto_create_schema = True

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def activate(self):
        self.is_active = True
        self.activated_at = timezone.now()
        self.save(update_fields=["is_active", "activated_at"])

    def suspend(self):
        self.is_active = False
        self.suspended_at = timezone.now()
        self.save(update_fields=["is_active", "suspended_at"])


class Domain(DomainMixin):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Domain"
        verbose_name_plural = "Domains"


class TenantProfile(models.Model):
    """Extended business info."""

    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="profile")

    admin_email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)

    logo = models.ImageField(blank=True, null=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
