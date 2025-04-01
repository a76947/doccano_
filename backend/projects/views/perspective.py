from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from projects.models import Perspective, Project, PerspectiveAnswer, PerspectiveGroup
from projects.serializers import PerspectiveSerializer, PerspectiveAnswerSerializer, PerspectiveGroupSerializer

class PerspectiveViewSet(viewsets.ModelViewSet):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [permissions.IsAuthenticated]


class PerspectiveAnswerViewSet(viewsets.ModelViewSet):
    serializer_class = PerspectiveAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get('project_id')
        return PerspectiveAnswer.objects.filter(project_id=project_id)

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
