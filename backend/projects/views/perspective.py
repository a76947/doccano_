from rest_framework import viewsets, permissions, status
from django.shortcuts import get_object_or_404
from projects.models import Perspective, Project, PerspectiveAnswer, PerspectiveGroup, Member
from projects.serializers import PerspectiveSerializer, PerspectiveAnswerSerializer, PerspectiveGroupSerializer
from django.conf import settings

class PerspectiveViewSet(viewsets.ModelViewSet):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [permissions.IsAuthenticated]


class PerspectiveAnswerViewSet(viewsets.ModelViewSet):
    serializer_class = PerspectiveAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        queryset = PerspectiveAnswer.objects.filter(project_id=project_id)
        
        # Filter by perspective (question) ID if provided
        perspective_id = self.request.query_params.get('perspective')
        if perspective_id:
            queryset = queryset.filter(perspective_id=perspective_id)
        
        # If user is admin, return all answers (with user information)
        if self._is_admin(project_id):
            return queryset.select_related('created_by')
        
        # Non-admin users can only see their own answers
        return queryset.filter(created_by=self.request.user)

    def _is_admin(self, project_id):
        """Check if the current user is an admin for this project"""
        # Super users are always considered admins
        if self.request.user.is_superuser:
            return True
            
        # Check if the user has admin role in this project
        project = get_object_or_404(Project, id=project_id)
        member = Member.objects.filter(project=project, user=self.request.user).first()
        
        # Make sure settings.ROLE_PROJECT_ADMIN is defined, otherwise use default 'project_admin'
        admin_role = getattr(settings, 'ROLE_PROJECT_ADMIN', 'project_admin')
        return member and member.role.name == admin_role

    def perform_create(self, serializer):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        serializer.save(
            project=project,
            created_by=self.request.user
        )


class PerspectiveGroupViewSet(viewsets.ModelViewSet):
    queryset = PerspectiveGroup.objects.all()
    serializer_class = PerspectiveGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return PerspectiveGroup.objects.filter(project_id=project_id)

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        serializer.save(project=project)
