from django.urls import path
from rest_framework import routers

from .views import PostCategoryViewSet, PostTagViewSet

router = routers.DefaultRouter(trailing_slash=False)

router.register("categories", PostCategoryViewSet, basename="blog_post_category")
router.register("tags", PostTagViewSet, basename="blog_post_tag")

# listing apis
list_urls = [
]

urlpatterns = [*list_urls, *router.urls]
