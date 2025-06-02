from rest_framework import serializers

from src.inventory.catalog.models import ProductCategory, ProductUnit


class ProductCategoryForProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "code", "icon"]


class ProductUnitForProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductUnit
        fields = ["id", "name", "short_form"]
