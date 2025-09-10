from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

User = get_user_model()

# Temporary in-memory storage for votes
votes = {"option1": 0, "option2": 0}

# In-memory storage for sessions
# In a production environment, this should be in a database
sessions = {}

class VotacoesSessionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id):
        """
        List all sessions for a project
        """
        project_sessions = [
            {**session, 'id': session_id} 
            for session_id, session in sessions.items() 
            if session['project_id'] == project_id
        ]
        return Response(project_sessions, status=status.HTTP_200_OK)
    
    def post(self, request, project_id):
        """
        Create a new session (admin only)
        """
        if not request.user.is_superuser and not self._is_project_admin(request.user, project_id):
            return Response(
                {"error": "Only administrators can create sessions"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        title = request.data.get('title')
        description = request.data.get('description', '')
        
        if not title:
            return Response(
                {"error": "Session title is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        session_id = str(uuid.uuid4())
        sessions[session_id] = {
            'project_id': project_id,
            'title': title,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'created_by': request.user.username,
            'votes': [],
            'messages': []
        }
        
        return Response(
            {"id": session_id, **sessions[session_id]}, 
            status=status.HTTP_201_CREATED
        )
    
    def _is_project_admin(self, user, project_id):
        # In a real implementation, check if user is admin for this project
        # This is a placeholder implementation
        return True  # For development purposes


class VotacoesSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id, session_id):
        """
        Get session details
        """
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(
            {"id": session_id, **sessions[session_id]}, 
            status=status.HTTP_200_OK
        )
    
    def delete(self, request, project_id, session_id):
        """
        Delete a session (admin only)
        """
        if not request.user.is_superuser and not self._is_project_admin(request.user, project_id):
            return Response(
                {"error": "Only administrators can delete sessions"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        del sessions[session_id]
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def patch(self, request, project_id, session_id):
        """
        Update a session (admin only)
        """
        if not request.user.is_superuser and not self._is_project_admin(request.user, project_id):
            return Response(
                {"error": "Only administrators can update sessions"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update the session with provided data
        if 'ended' in request.data:
            sessions[session_id]['ended'] = request.data['ended']
        
        return Response(
            {"id": session_id, **sessions[session_id]}, 
            status=status.HTTP_200_OK
        )
    
    def _is_project_admin(self, user, project_id):
        # Placeholder implementation
        return True


class VotacoesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id, session_id):
        """
        Get all votes for a session
        """
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(sessions[session_id]['votes'], status=status.HTTP_200_OK)
    
    def post(self, request, project_id, session_id):
        """
        Create a new vote in a session (admin only)
        """
        if not request.user.is_superuser and not self._is_project_admin(request.user, project_id):
            return Response(
                {"error": "Only administrators can create votes"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        title = request.data.get('title')
        description = request.data.get('description', '')
        options = request.data.get('options', [])
        
        if not title or not options:
            return Response(
                {"error": "Vote title and options are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        vote_id = str(uuid.uuid4())
        vote = {
            'id': vote_id,
            'title': title,
            'description': description,
            'options': options,
            'created_at': datetime.now().isoformat(),
            'created_by': request.user.username,
            'results': {option: 0 for option in options}
        }
        
        sessions[session_id]['votes'].append(vote)
        return Response(vote, status=status.HTTP_201_CREATED)
    
    def _is_project_admin(self, user, project_id):
        # Placeholder implementation
        return True


class VoteSubmissionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, project_id, session_id, vote_id):
        """
        Submit a vote for a specific option
        """
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Find the vote in the session
        vote = None
        for v in sessions[session_id]['votes']:
            if v['id'] == vote_id:
                vote = v
                break
        
        if not vote:
            return Response(
                {"error": "Vote not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        option = request.data.get("option")
        if option not in vote['options']:
            return Response(
                {"error": "Invalid option"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        vote['results'][option] += 1
        return Response(
            {"message": "Vote registered successfully", "results": vote['results']}, 
            status=status.HTTP_200_OK
        )


class SessionChatView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id, session_id):
        """
        Get all messages for a session
        """
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        return Response(sessions[session_id]['messages'], status=status.HTTP_200_OK)
    
    def post(self, request, project_id, session_id):
        """
        Add a message to a session chat
        """
        if session_id not in sessions or sessions[session_id]['project_id'] != project_id:
            return Response(
                {"error": "Session not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        user = request.user.username
        message = request.data.get("message")
        
        if not message:
            return Response(
                {"error": "Message cannot be empty"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        new_message = {
            'id': str(uuid.uuid4()),
            'user': user,
            'text': message,
            'timestamp': datetime.now().isoformat()
        }
        
        sessions[session_id]['messages'].append(new_message)
        return Response(new_message, status=status.HTTP_201_CREATED)