from django.urls import include, path
from .views import Me, UserCreation, Users, UserRetrieveUpdate

urlpatterns = [
    # /v1/me  -> dados do usuário logado
    path("me", Me.as_view(), name="me"),

    # /v1/users  -> listagem
    path("users", Users.as_view(), name="user_list"),

    # /v1/users/create -> criar usuário
    path("users/create", UserCreation.as_view(), name="user_create"),

    # /v1/users/<id>/ -> ver/editar/deletar um usuário específico
    path("users/<int:pk>/", UserRetrieveUpdate.as_view(), name="user_detail"),

    # /v1/auth/... -> endpoints de auth (dj_rest_auth)
    path("auth/", include("dj_rest_auth.urls")),
]
