from django.urls import include, path

app_label = ["internal"]

urlpatterns = [
    path("user-mod/", include("src.user.urls"), name="user-mod"),
]
