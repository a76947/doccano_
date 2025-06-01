from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.perspective import PerspectiveViewSet, PerspectiveGroupViewSet, PerspectiveAnswerViewSet
from .views.project import ProjectList, ProjectDetail, CloneProject
from .views.votacoes import VotacoesView
from .views.project import DiscrepancyAnalysisView, ProjectList, ProjectDetail, CloneProject
from .views.tag import TagList, TagDetail
from .views.member import MemberList, MemberDetail, MyRole
from .views.permissions import MyProjectPermissions  # Import from the new file
from .views.annotation import UserAnnotationsAPI
from .views.chat import ChatMessagesView
from .views.rules import RulesToSubmitAnalysisView, RulesSubmitedAnalysisView
from projects.views.votation import VotingSessionView, VotingSessionAnswerView, VotingSessionUserAnswersView

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
    path('projects/<int:project_id>/annotations', UserAnnotationsAPI.as_view(), name='user_annotations'),
    path("projects/<int:project_id>/votacoes", VotacoesView.as_view(), name="votacoes"),
    path("projects/<int:project_id>/chat", ChatMessagesView.as_view(), name="chat_messages"),

    path("projects/<int:project_id>/discrepacies", DiscrepancyAnalysisView.as_view(), name="discrepancy_analysis"),
    
    path("projects/<int:project_id>/rules/tosubmit", RulesToSubmitAnalysisView.as_view(), name="tosubmit_questions"),
    path("projects/<int:project_id>/rules/submited", RulesSubmitedAnalysisView.as_view(), name="submited_questions"),
    
    path("projects/<int:project_id>/rules/tosubmit/<int:question_id>/", RulesToSubmitAnalysisView.as_view(), name="tosubmit_questions_delete"),

    path("projects/<int:project_id>/votingsessions", VotingSessionView.as_view(), name="voting_sessions"),

    path("projects/<int:project_id>/votingsessions/<int:questions_id>/", VotingSessionView.as_view(), name="voting_session_detail"),

    path("projects/<int:project_id>/votingsessions/<int:questions_id>/answers", VotingSessionAnswerView.as_view(), name="voting_session_answers"),

    path("projects/<int:project_id>/votingsessions/<int:voting_session_id>/user-answers", VotingSessionUserAnswersView.as_view(), name="voting_session_user_answers"),

]
