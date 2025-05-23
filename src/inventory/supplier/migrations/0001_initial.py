# Generated by Django 5.1.4 on 2025-05-05 11:04

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InvSupplier",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Represents unique uuid.",
                        unique=True,
                        verbose_name="uuid",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created date",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="date updated"),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this object should be treated as active. Unselect this instead of deleting instances.",
                        verbose_name="active",
                    ),
                ),
                (
                    "is_archived",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether this object should be treated as delected. Unselect this instead of deleting instances.",
                        verbose_name="archived",
                    ),
                ),
                (
                    "opening_balance",
                    models.DecimalField(
                        decimal_places=2,
                        default=0.0,
                        help_text="Initial balance amount (default: 0.00).",
                        max_digits=12,
                        verbose_name="Opening Balance",
                    ),
                ),
                (
                    "remarks",
                    models.CharField(
                        blank=True,
                        help_text="Optional remarks about the supplier.",
                        max_length=255,
                        verbose_name="Remarks",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        help_text="Link to the user account of the supplier (optional).",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="inv_supplier",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="User",
                    ),
                ),
            ],
            options={
                "verbose_name": "Inventory Supplier",
                "verbose_name_plural": "Inventory Suppliers",
                "ordering": ["-id"],
            },
        ),
    ]
