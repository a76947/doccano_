from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from labels.models import Category  # ou Span, TextLabel, etc.
from labels.serializers import CategorySerializer  # usa o serializer certo
from projects.permissions import IsProjectMember

class ProjectLabelListAPI(APIView):
    permission_classes = [IsAuthenticated & IsProjectMember]

    def get(self, request, project_id):
        labels = Category.objects.filter(example__project_id=project_id).values('label__text').distinct()
        # Devolve apenas os textos únicos
        data = [{'text': label['label__text']} for label in labels if label['label__text']]
        return Response(data)
