from rest_framework import serializers

from ..models import Post, PostCategory
from ...core.constants import MAX_PUBLIC_POST_TAG_LIMIT, MAX_PUBLIC_POST_CATEGORY_LIMIT


class PublicPostsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            "uuid",
            "title",
            "slug",
            "format",
            "excerpt",
            "read_time",
            "published_at",
            "views"
        ]


class PublicPostCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(),
        max_length=MAX_PUBLIC_POST_TAG_LIMIT
    )
    categories = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=PostCategory.objects.filter(is_active=True)
        ), max_length=MAX_PUBLIC_POST_CATEGORY_LIMIT
    )

    class Meta:
        model = Post
        fields = [
            "title",
            "tags",
            "content",
            "cover_image",
            "status",
            "format",
            "visibility",
            "read_time",
            "categories",
            "allow_comments",
        ]


