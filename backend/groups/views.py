from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import GroupSerializer


class GroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        groups = GroupService.list_groups()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
