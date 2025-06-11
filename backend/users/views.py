from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveDestroyAPIView
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from projects.models import Project
from .serializers import UserSerializer
from projects.permissions import IsProjectAdmin
from dj_rest_auth.registration.serializers import RegisterSerializer

class UsersWithProjectsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projetos = Project.objects.all()

        # DEBUG: Ver todos os criadores dos projetos
        print("📦 Projetos encontrados:", projetos.count())
        for p in projetos:
            print(f"🔍 Projeto: {p.name} | Criado por: {p.created_by} (ID: {p.created_by_id})")

        user_ids = (
            Project.objects.exclude(created_by=None)
            .values_list('created_by_id', flat=True)
            .distinct()
        )

        print("✅ IDs de utilizadores com projetos:", list(user_ids))
        return Response(user_ids)

class Me(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data)

class Users(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ("auth_user",)

class UserCreation(generics.CreateAPIView):
    serializer_class = CustomRegisterSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # user pode vir como (user,) se o serializer retornar tupla
        if isinstance(user, tuple):
            user = user[0]
        
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):
        user = serializer.save(self.request)
        return user

class UserDetail(RetrieveDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        user = self.get_object()

        if Project.objects.filter(created_by=user).exists():
            return Response(
                {"detail": "Cannot delete user with projects."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().delete(request, *args, **kwargs)
