from django.urls import path, include

urlpatterns = [
    # Todo o "v1" fica dentro de users.urls
    path("v1/", include("backend.users.urls")),
    path("v2/", include("perfis.urls")),
]
