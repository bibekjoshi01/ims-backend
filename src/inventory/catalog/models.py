# Django Imports
from django.db import models
from django.utils.translation import gettext_lazy as _

# Project Imports
from src.base.models import AbstractInfoModel


class ProductCategory(AbstractInfoModel):
    """
    Represents an category for organizing inventory products.
    """

    name = models.CharField(
        _("Category Name"),
        max_length=100,
        help_text=_("Name of the category."),
    )
    code = models.CharField(
        _("Category Code"),
        max_length=20,
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
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


class Product(AbstractInfoModel):
    """
    Represents a product available for sale.
    """

    name = models.CharField(
        _("Name"),
        max_length=150,
        help_text=_("Represents Product name."),
    )
    sku = models.CharField(
        _("Stock Keeping Unit"),
        max_length=255,
        blank=True,
        help_text=_(
            "The stock keeping unit (unique identifier for inventory management).",
        ),
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
        verbose_name=_("Category"),
        help_text=_("Category to which this product belongs."),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Detailed product description."),
    )
    image = models.ImageField(
        _("Image"),
        upload_to="catalog/products/",
        null=True,
        help_text=_("Main product image."),
    )
    selling_price = models.DecimalField(
        _("Selling Price"),
        max_digits=12,
        decimal_places=2,
        default=0.0,
        help_text=_("Selling price without taxes."),
    )

    class Meta:
        ordering = ["name"]
        verbose_name = _("Product")
        verbose_name_plural = _("Products")

    def __str__(self):
        return f"{self.name}"
