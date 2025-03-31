from django.urls import path
from .views import GroupListView

urlpatterns = [
    path('groups', GroupListView.as_view(), name='group-list'),
]
