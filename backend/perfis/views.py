from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.models import Permission, Group
from django.shortcuts import get_object_or_404
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

class GroupDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        serializer = GroupSerializer(group)
        return Response(serializer.data)

    def put(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        serializer = GroupSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            permissions_data = request.data.get('permissions')
            if permissions_data is not None:
                group.permissions.set(permissions_data)
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        group = get_object_or_404(Group, pk=pk)
        group.delete()
        return Response(status=204)

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