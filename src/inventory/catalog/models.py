# Django Imports
from django.db import models
from django.utils.translation import gettext_lazy as _

# Project Imports
from src.base.models import AbstractInfoModel


class ItemCategory(AbstractInfoModel):
    """
    Represents an category for organizing inventory items.
    """

    name = models.CharField(
        _("Category Name"),
        max_length=100,
        help_text=_("Name of the category."),
    )
    code = models.CharField(
        _("Category Code"),
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_("Unique code for identifying the category."),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Optional detailed description of the category."),
    )
    icon = models.ImageField(
        _("Category Icon"),
        upload_to="catalog/categories/",
        null=True,
        help_text=_("Optional icon representing the category."),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Item Category")
        verbose_name_plural = _("Item Categories")

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


class Item(AbstractInfoModel):
    """
    Represents a product/item available for sale.
    """

    name = models.CharField(
        _("Name"),
        max_length=150,
        help_text=_("Represents Item name."),
    )
    sku = models.CharField(
        _("Stock Keeping Unit"),
        max_length=255,
        unique=True,
        help_text=_(
            "The stock keeping unit (unique identifier for inventory management).",
        ),
    )
    category = models.ForeignKey(
        _("Category"),
        ItemCategory,
        on_delete=models.PROTECT,
        related_name="items",
        help_text=_("Category to which this item belongs."),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Detailed product description."),
    )
    image = models.ImageField(
        _("Image"),
        upload_to="catalog/items/",
        blank=True,
        null=True,
        help_text=_("Main product image."),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Item")
        verbose_name_plural = _("Items")

    def __str__(self):
        return f"{self.name}"
