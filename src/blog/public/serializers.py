from rest_framework import serializers

from src.blog.models import Post, PostCategory


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
            "views",
        ]


class PublicPostCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(),
    )
    categories = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=PostCategory.objects.filter(is_active=True),
        ),
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
