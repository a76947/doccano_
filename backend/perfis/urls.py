from django.urls import path
from .views import PermissionListView, GroupListView, GroupCreateView

urlpatterns = [
    path('permissions/', PermissionListView.as_view(), name='permission-list'),
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('groups/create/', GroupCreateView.as_view(), name='group-create'),
]