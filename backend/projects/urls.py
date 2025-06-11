from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.perspective import PerspectiveViewSet, PerspectiveGroupViewSet, PerspectiveAnswerViewSet
from .views.project import DiscrepancyAnalysisView, ProjectList, ProjectDetail, CloneProject

from .views.votacoes import VotacoesView
from .views.tag import TagList, TagDetail
from .views.member import MemberList, MemberDetail, MyRole
from .views.permissions import MyProjectPermissions  # Import from the new file
from .views.annotation import UserAnnotationsAPI
from .views.chat import ChatMessagesView


# Create router for ViewSets
router = DefaultRouter()
# These patterns will be prefixed by 'v1/' in the main urls.py, so DON'T include 'v1/' here
router.register(r'projects/(?P<project_id>\d+)/perspectives', PerspectiveViewSet, basename='perspective')
router.register(r'projects/(?P<project_id>\d+)/perspective-groups', PerspectiveGroupViewSet, basename='perspective-group')
router.register(r'projects/(?P<project_id>\d+)/perspective-answers', PerspectiveAnswerViewSet, 'perspective-answer')

urlpatterns = [
    # Include router URLs directly (not under another path)
    path('', include(router.urls)),
    
    # Other URL patterns
    path("projects", ProjectList.as_view(), name="project_list"),
    path("projects/<int:project_id>", ProjectDetail.as_view(), name="project_detail"),
    path("projects/<int:project_id>/my-role", MyRole.as_view(), name="my_role"),
    path("projects/<int:project_id>/tags", TagList.as_view(), name="tag_list"),
    path("projects/<int:project_id>/tags/<int:tag_id>", TagDetail.as_view(), name="tag_detail"),
    path("projects/<int:project_id>/members", MemberList.as_view(), name="member_list"),
    path("projects/<int:project_id>/members/<int:member_id>", MemberDetail.as_view(), name="member_detail"),
    path("projects/<int:project_id>/clone", CloneProject.as_view(), name="clone_project"),
    path('projects/<int:project_id>/my-permissions/', MyProjectPermissions.as_view(), name='my-project-permissions'),



    path("projects/<int:project_id>/discrepacies", DiscrepancyAnalysisView.as_view(), name="discrepancy_analysis"),

    path('projects/<int:project_id>/annotations', UserAnnotationsAPI.as_view(), name='user_annotations'),
    path("projects/<int:project_id>/votacoes", VotacoesView.as_view(), name="votacoes"),
    path("projects/<int:project_id>/chat", ChatMessagesView.as_view(), name="chat_messages"),

]
