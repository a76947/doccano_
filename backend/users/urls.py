from django.urls import include, path
from .views import Me, UserCreation, Users, UserRetrieveUpdateDestroy

urlpatterns = [
    path("me", Me.as_view(), name="me"),
    path("users", Users.as_view(), name="user_list"),
    path("users/create", UserCreation.as_view(), name="user_create"),
    # /v1/users/<id>/ -> GET, PUT/PATCH, DELETE
    path("users/<int:id>/", UserRetrieveUpdateDestroy.as_view(), name="user_detail"),
    path("auth/", include("dj_rest_auth.urls")),
]
