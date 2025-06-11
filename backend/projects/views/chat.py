from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

chat_messages = {}  # Dictionary to store messages by project

class ChatMessagesView(APIView):
    """
    API endpoint for chat messages.
    """
    # Add permission_classes to ensure authentication is required
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id):
        print(f"DEBUG: ChatMessagesView.get() called for project {project_id}")
        # Initialize message list for this project if it doesn't exist
        if project_id not in chat_messages:
            chat_messages[project_id] = []
        return Response(chat_messages[project_id], status=status.HTTP_200_OK)

    def post(self, request, project_id):
        print(f"DEBUG: ChatMessagesView.post() called with data: {request.data}")
        # Initialize message list for this project if it doesn't exist
        if project_id not in chat_messages:
            chat_messages[project_id] = []
            
        message = request.data.get("message")
        user = request.data.get("user")
        
        if message and user:
            chat_messages[project_id].append({"user": user, "text": message})
            return Response({"message": "Message added successfully"}, status=status.HTTP_201_CREATED)
        return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)