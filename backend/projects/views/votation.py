from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status, permissions
from projects.models import VotingSession

class VotingSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        sessions = VotingSession.objects.filter(project_id=project_id)
        if not sessions.exists():
            raise NotFound("No voting sessions found for this project.")
        
        sessions_list = [{
            "id": session.id,
            "questions": session.questions,
            "created_at": session.created_at,
            "vote_end_date": session.vote_end_date,
            "finish": session.finish,
        } for session in sessions]
        
        return Response({"voting_sessions": sessions_list}, status=status.HTTP_200_OK)

    def post(self, request, project_id):
        """
        Cria uma nova sessão de votação para o projeto.
        Parâmetros esperados no body (JSON):
          - questions: lista de strings (opcional)
          - vote_end_date: data final da votação (opcional)
          - finish: campo booleano para status (opcional)
        """
        questions = request.data.get("questions", [])
        vote_end_date = request.data.get("vote_end_date", None)
        finish = request.data.get("finish", False)
        
        session = VotingSession.objects.create(
            project_id=project_id,
            questions=questions,
            vote_end_date=vote_end_date,
            finish=finish
        )
        
        return Response({
            "id": session.id,
            "questions": session.questions,
            "created_at": session.created_at,
            "vote_end_date": session.vote_end_date,
            "finish": session.finish,
        }, status=status.HTTP_201_CREATED)