from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status, permissions
from projects.models import VotingSession, VotingSessionAnswer

class VotingSessionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id, questions_id=None):
        if questions_id is not None:
            try:
                session = VotingSession.objects.get(project_id=project_id, id=questions_id)
                data = {
                    "id": session.id,
                    "questions": session.questions,
                    "created_at": session.created_at,
                    "vote_end_date": session.vote_end_date,
                    "finish": session.finish,
                }
                return Response(data, status=status.HTTP_200_OK)
            except VotingSession.DoesNotExist:
                raise NotFound("Voting session not found for this project.")
        else:
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
    
    def put(self, request, project_id, questions_id):
        try:
            session = VotingSession.objects.get(project_id=project_id, id=questions_id)
            session.finish = True
            session.save()
            return Response({"id": session.id, "finish": session.finish}, status=status.HTTP_200_OK)
        except VotingSession.DoesNotExist:
            return Response({"error": "Voting session not found."}, status=status.HTTP_404_NOT_FOUND)
        
class VotingSessionAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id, questions_id):
        try:
            answer_obj = VotingSessionAnswer.objects.get(project_id=project_id, id=questions_id)
            data = {
                "id": answer_obj.id,
                "voting_session": answer_obj.voting_session.id,
                "project": answer_obj.project.id,
                "created_by": answer_obj.created_by.id if answer_obj.created_by else None,
                "answer": answer_obj.answer,  # Lista de strings
            }
            return Response(data, status=status.HTTP_200_OK)
        except VotingSessionAnswer.DoesNotExist:
            raise NotFound("Voting session answer not found for this project.")
        
    def post(self, request, project_id, questions_id):
        answer = request.data.get("answer", [])

        session_answer = VotingSessionAnswer.objects.create(
            project_id=project_id,
            voting_session_id=questions_id,
            created_by=request.user,
            answer=answer
        )

        return Response({
            "id": session_answer.id,
            "voting_session": session_answer.voting_session.id,
            "project": session_answer.project.id,
            "created_by": session_answer.created_by.id
        }, status=status.HTTP_201_CREATED)