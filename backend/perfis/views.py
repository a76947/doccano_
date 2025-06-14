from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.models import Permission, Group
from .serializers import PermissionSerializer, GroupSerializer

class GroupListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        groups = Group.objects.prefetch_related('permissions').all()
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)

class GroupCreateView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        data = request.data
        group = Group.objects.create(name=data['name'])
        group.permissions.set(data['permissions'])
        group.save()
        serializer = GroupSerializer(group)
        return Response(serializer.data)

class PermissionListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        permissions = Permission.objects.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)

class GroupDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, group_id):
        try:
            group = Group.objects.get(id=group_id)
            group.delete()
            return Response(status=204)
        except Group.DoesNotExist:
            return Response(status=404)