from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import permissions, status
from projects.models import ToSubmitQuestions

class RulesToSubmitAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        rules = ToSubmitQuestions.objects.filter(project_id=project_id, status="toSubmit")
        if not rules.exists():
            raise NotFound("No rules found for this project.")

        # Monta a lista de regras para a tabela de frontend
        rules_list = [{
            "id": rule.id,
            "regra": rule.question,
        } for rule in rules]
        
        return Response({"rules": rules_list})
    
    def post(self, request, project_id):
        question = request.data.get("question")
        if not question:
            return Response({"error": "Question field is required."}, status=status.HTTP_400_BAD_REQUEST)
        new_rule = ToSubmitQuestions.objects.create(project_id=project_id, question=question, status="toSubmit")
        
        return Response({"id": new_rule.id, "regra": new_rule.question}, status=status.HTTP_201_CREATED)
    
    def delete(self, request, project_id, question_id):
        try:
            rule = ToSubmitQuestions.objects.get(project_id=project_id, id=question_id)
            rule.delete()
            return Response({"message": "Rule deleted successfully."}, status=status.HTTP_200_OK)
        except ToSubmitQuestions.DoesNotExist:
            return Response({"error": "Rule not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, project_id, question_id):
        question = request.data.get("question")
        if not question:
            return Response({"error": "Question field is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rule = ToSubmitQuestions.objects.get(project_id=project_id, id=question_id)
            rule.question = question
            rule.save()
            return Response({"id": rule.id, "regra": rule.question}, status=status.HTTP_200_OK)
        except ToSubmitQuestions.DoesNotExist:
            return Response({"error": "Rule not found."}, status=status.HTTP_404_NOT_FOUND)

class RulesSubmitedAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, project_id):
        rules = ToSubmitQuestions.objects.filter(project_id=project_id, status="submited")
        if not rules.exists():
            raise NotFound("No rules found for this project.")

        # Monta a lista de regras para a tabela de frontend
        rules_list = [{
            "id": rule.id,
            "regra": rule.question,
        } for rule in rules]
        
        return Response({"rules": rules_list})