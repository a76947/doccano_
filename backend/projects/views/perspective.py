from rest_framework import viewsets, permissions
from django.shortcuts import get_object_or_404
from projects.models import Perspective, PerspectiveQuestion, Project, PerspectiveAnswer
from projects.serializers import PerspectiveQuestionSerializer, PerspectiveSerializer, PerspectiveAnswerSerializer

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

class PerspectiveQuestionViewSet(viewsets.ModelViewSet):
    queryset = PerspectiveQuestion.objects.all()
    serializer_class = PerspectiveQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Certifique-se de que o parâmetro `project_id` está sendo usado corretamente
        perspective_id = self.kwargs.get("perspective_id")
        return PerspectiveQuestion.objects.filter(perspective_id=perspective_id)

    def perform_create(self, serializer):
        # Certifique-se de que o parâmetro `perspective_id` está sendo passado corretamente
        perspective_id = self.kwargs.get("perspective_id")
        perspective = get_object_or_404(Perspective, id=perspective_id)
        serializer.save(perspective=perspective, created_by=self.request.user)