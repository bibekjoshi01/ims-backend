from django_filters.filterset import FilterSet
from .models import PostTag, PostCategory


class FilterForPostCategoryViewSet(FilterSet):
    """Filters for Blog Post Cateogry"""

    class Meta:
        model = PostCategory
        fields = ["name", "is_active", "parent"]


class FilterForPostTagViewSet(FilterSet):
    """Filters for Blog Post Tag"""

    class Meta:
        model = PostTag
        fields = ["name", "is_active"]
