from rest_framework import viewsets, permissions
from projects.models import DiscrepanciesQuestions
from projects.serializers import DiscrepanciesQuestionsSerializer

class DiscrepancyAnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = DiscrepanciesQuestionsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Retorna todos os registros da tabela para o usuário logado (ou aplique filtragem conforme necessário)
        return DiscrepanciesQuestions.objects.all()