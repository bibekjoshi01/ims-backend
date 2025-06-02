from rest_framework import serializers

# Project Imports
from src.base.serializers import AbstractInfoRetrieveSerializer
from src.inventory.utils.validators import validate_amount
from src.libs.get_context import get_user_by_context
from src.libs.validators import validate_unique_fields

from .listing_apis.serializers import (
    ProductCategoryForProductListSerializer,
    ProductUnitForProductListSerializer,
)
from .messages import CATEGORY_CREATE_SUCCESS, CATEGORY_UPDATE_SUCCESS
from .models import Product, ProductCategory, ProductUnit

# ------------------------------------------------------------------------
# Product Category
# ------------------------------------------------------------------------


class ProductCategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "name", "code", "icon", "is_active"]


class ProductCategoryRetrieveSerializer(AbstractInfoRetrieveSerializer):
    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = ProductCategory
        custom_fields = ["id", "name", "code", "icon", "description"]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class ProductCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["name", "code", "icon", "description", "is_active"]

    def validate(self, attrs):
        return validate_unique_fields(
            model=ProductCategory,
            attrs=attrs,
            fields=["name", "code"],
            field_transform_map={
                "name": lambda x: x.lower().strip(),
                "code": lambda x: x.strip(),
            },
        )

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        return ProductCategory.objects.create(
            created_by=created_by,
            **validated_data,
        )

    def to_representation(self, instance):
        return {"id": instance.id, "message": CATEGORY_CREATE_SUCCESS}


class ProductCategoryPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["name", "code", "icon", "description", "is_active"]

    def validate(self, attrs):
        return validate_unique_fields(
            model=ProductCategory,
            attrs=attrs,
            instance=self.instance,
            fields=["name", "code"],
            field_transform_map={
                "name": lambda x: x.lower().strip(),
                "code": lambda x: x.strip(),
            },
        )

    def update(self, instance, validated_data):
        validated_data["updated_by"] = get_user_by_context(self.context)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save(update_fields=validated_data.keys())
        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": CATEGORY_UPDATE_SUCCESS}


# ------------------------------------------------------------------------
# Product
# ------------------------------------------------------------------------


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "image",
            "category",
            "unit",
            "selling_price",
            "stock_alert_qty",
            "is_active",
        ]


class ProductRetrieveSerializer(AbstractInfoRetrieveSerializer):
    category = ProductCategoryForProductListSerializer()
    unit = ProductUnitForProductListSerializer()

    class Meta(AbstractInfoRetrieveSerializer.Meta):
        model = Product
        custom_fields = [
            "id",
            "name",
            "sku",
            "image",
            "category",
            "unit",
            "selling_price",
            "stock_alert_qty",
            "barcode",
            "description",
        ]

        fields = custom_fields + AbstractInfoRetrieveSerializer.Meta.fields


class ProductCreateSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.filter(is_active=True),
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=ProductUnit.objects.filter(is_active=True),
    )
    selling_price = serializers.DecimalField(
        validators=[validate_amount],
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "image",
            "category",
            "unit",
            "selling_price",
            "stock_alert_qty",
            "barcode",
            "description",
        ]

    def validate(self, attrs):
        return validate_unique_fields(
            model=Product,
            attrs=attrs,
            fields=["sku"],
            field_transform_map={"sku": lambda x: x.strip()},
        )

    def create(self, validated_data):
        created_by = get_user_by_context(self.context)
        return Product.objects.create(
            created_by=created_by,
            **validated_data,
        )

    def to_representation(self, instance):
        return {"id": instance.id, "message": CATEGORY_CREATE_SUCCESS}


class ProductPatchSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(
        queryset=ProductCategory.objects.filter(is_active=True),
    )
    unit = serializers.PrimaryKeyRelatedField(
        queryset=ProductUnit.objects.filter(is_active=True),
    )
    selling_price = serializers.DecimalField(
        validators=[validate_amount],
        max_digits=12,
        decimal_places=2,
    )

    class Meta:
        model = Product
        fields = [
            "name",
            "sku",
            "image",
            "category",
            "unit",
            "selling_price",
            "stock_alert_qty",
            "barcode",
            "description",
        ]

    def validate(self, attrs):
        return validate_unique_fields(
            model=Product,
            attrs=attrs,
            instance=self.instance,
            fields=["sku"],
            field_transform_map={"sku": lambda x: x.strip()},
        )

    def update(self, instance, validated_data):
        validated_data["updated_by"] = get_user_by_context(self.context)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save(update_fields=validated_data.keys())
        return instance

    def to_representation(self, instance):
        return {"id": instance.id, "message": CATEGORY_UPDATE_SUCCESS}
