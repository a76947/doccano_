from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from projects.models import RuleDiscussionMessage
from projects.serializers import RuleDiscussionSerializer


class RuleDiscussionView(APIView):
    """API endpoint to list or create discussion messages for rules."""
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        session_id = request.query_params.get('session_id')
        question_index = request.query_params.get('question_index')
        queryset = RuleDiscussionMessage.objects.filter(project_id=project_id)
        if session_id is not None:
            queryset = queryset.filter(voting_session_id=session_id)
        if question_index is not None:
            queryset = queryset.filter(question_index=question_index)
        serializer = RuleDiscussionSerializer(queryset.order_by('created_at'), many=True)
        return Response({'messages': serializer.data})

    def post(self, request, project_id):
        session_id = request.data.get('session_id')
        question_index = request.data.get('question_index')
        message = request.data.get('message')
        if session_id is None or question_index is None or message is None:
            return Response({'detail': 'session_id, question_index and message are required.'},
                            status=status.HTTP_400_BAD_REQUEST)
        obj = RuleDiscussionMessage.objects.create(
            project_id=project_id,
            voting_session_id=session_id,
            question_index=question_index,
            message=message,
            created_by=request.user
        )
        serializer = RuleDiscussionSerializer(obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED) 