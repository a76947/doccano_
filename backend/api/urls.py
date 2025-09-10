from django.urls import path, include

from api.views import TaskStatus

urlpatterns = [
    # Todo o "v1" fica dentro de users.urls
    path("v1/", include("backend.users.urls")),
    path("v2/", include("perfis.urls")),
    path("tasks/status/<uuid:task_id>", TaskStatus.as_view(), name="task_status"),
]
