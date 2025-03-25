from django.urls import include, path
from .views import Me, UserCreation, Users, UserRetrieveUpdateDestroy  # Ensuring consistency with naming

urlpatterns = [
    # /v1/me -> Dados do usuário logado
    path("me", Me.as_view(), name="me"),

    # /v1/users -> Listagem de usuários
    path("users", Users.as_view(), name="user_list"),

    # /v1/users/create -> Criar usuário
    path("users/create", UserCreation.as_view(), name="user_create"),

    # /v1/users/<id>/ -> Ver/editar/deletar um usuário específico
    path("users/<int:pk>/", UserRetrieveUpdateDestroy.as_view(), name="user_detail"),

    # /v1/auth/... -> Endpoints de autenticação (dj_rest_auth)
    path("auth/", include("dj_rest_auth.urls")),
]
