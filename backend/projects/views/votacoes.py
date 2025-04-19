from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Temporary in-memory storage for votes
votes = {"option1": 0, "option2": 0}

class VotacoesView(APIView):
    def get(self, request, project_id):
        """
        Retrieve the current vote counts.
        """
        return Response(votes, status=status.HTTP_200_OK)

    def post(self, request, project_id):
        """
        Submit a vote for a specific option.
        """
        option = request.data.get("option")
        if option in votes:
            votes[option] += 1
            return Response({"message": "Vote registered successfully", "votes": votes}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid option"}, status=status.HTTP_400_BAD_REQUEST)