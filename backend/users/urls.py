from django.urls import include, path

from .views import Me, UserCreation, Users, UserDetail, UsersWithProjectsView

urlpatterns = [
    path(route="me", view=Me.as_view(), name="me"),
    path(route="users", view=Users.as_view(), name="user_list"),
    path(route="users/create", view=UserCreation.as_view(), name="user_create"),
    path(route="users/<int:id>", view=UserDetail.as_view(), name="user_detail"),
    path('users/with-projects/', UsersWithProjectsView.as_view(), name='users-with-projects'),
    path("auth/", include("dj_rest_auth.urls")),
]
