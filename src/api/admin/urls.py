from django.urls import include, path

app_label = ["admin"]

urlpatterns = [
    path("blog-app/", include("src.blog.urls")),
    path("user-app/", include("src.user.urls")),
]
