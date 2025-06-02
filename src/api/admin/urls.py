from django.urls import include, path

app_label = ["admin"]

urlpatterns = [
    path("user-app/", include("src.user.urls")),
    path("blog-app/", include("src.blog.urls")),
    path("supplier-mod/", include("src.supplier.urls")),
]
