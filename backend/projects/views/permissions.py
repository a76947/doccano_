from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from ..models import Project, Member

class MyProjectPermissions(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        """Get the current user's permissions for a specific project"""
        project = get_object_or_404(Project, pk=project_id)
        
        # Get the member object for this user in this project
        member = Member.objects.filter(user=request.user, project=project).first()
        
        if not member:
            return Response({"detail": "You are not a member of this project"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        # Check the role
        role = member.role
        
        # Return permissions based on role
        return Response({
            "isAdmin": role.name == "admin" or role.name == "project_admin",
            "role": role.name,
            "canCreateQuestions": role.name == "admin" or role.name == "project_admin",
            "canDeleteQuestions": role.name == "admin" or role.name == "project_admin", 
            "canAnswerQuestions": True  # Allow all project members to answer questions
        })