from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from projects.models import Perspective, Project, PerspectiveAnswer
from projects.serializers import PerspectiveSerializer, PerspectiveAnswerSerializer

class PerspectiveViewSet(viewsets.ModelViewSet):
    queryset = Perspective.objects.all()
    serializer_class = PerspectiveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return Perspective.objects.filter(project_id=project_id)

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)

        # Define opções automaticamente se o tipo for booleano
        if serializer.validated_data.get("data_type") == "boolean":
            serializer.validated_data["options"] = ["true", "false"]

        serializer.save(project=project)

class PerspectiveAnswerViewSet(viewsets.ModelViewSet):
    queryset = PerspectiveAnswer.objects.all()
    serializer_class = PerspectiveAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        project_id = self.kwargs.get("project_id")  # Corrige o nome do parâmetro
        return PerspectiveAnswer.objects.filter(project_id=project_id)

    def perform_create(self, serializer):
        project_id = self.kwargs.get("project_id")  # Corrige o nome do parâmetro
        project = get_object_or_404(Project, id=project_id)
        serializer.save(project=project, created_by=self.request.user)
