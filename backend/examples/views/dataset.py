from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from projects.permissions import IsProjectMember
from examples.models import Example

class DatasetListView(APIView):
    permission_classes = [IsAuthenticated & IsProjectMember]

    def get(self, request, project_id: int):
        datasets = (
            Example.objects.filter(project_id=project_id)
            .values_list("upload_name", flat=True)
            .distinct()
        )
        return Response([{"text": name, "value": name} for name in datasets]) 