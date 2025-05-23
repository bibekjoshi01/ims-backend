from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import AbstractInfoModel, PublicAbstractInfoModel


class AbstractInfoRetrieveSerializer(ModelSerializer):
    created_by_username = serializers.ReadOnlyField(source="created_by.username")
    updated_by_username = serializers.ReadOnlyField(source="updated_by.username")
    created_by_full_name = serializers.SerializerMethodField()
    updated_by_full_name = serializers.SerializerMethodField()

    class Meta:
        model = AbstractInfoModel
        fields = [
            "created_by",
            "created_by_username",
            "updated_by_username",
            "created_by_full_name",
            "updated_by_full_name",
            "created_at",
            "updated_at",
            "is_active",
        ]

    def get_created_by_full_name(
        self,
        obj,
    ) -> str:
        return obj.created_by.get_full_name()

    def get_updated_by_full_name(
        self,
        obj,
    ) -> str:
        if obj.updated_by:
            return obj.updated_by.get_full_name()

        return ""


class PublicAbstractInfoRetrieveSerializer(ModelSerializer):
    class Meta:
        model = PublicAbstractInfoModel
        fields = ["created_at", "updated_at", "is_active"]
