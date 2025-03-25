
from .serializers import CustomRegisterSerializer, UserSerializer

from .serializers import CustomRegisterSerializer

from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.generics import RetrieveUpdateDestroyAPIView

from rest_framework.generics import RetrieveDestroyAPIView
from django.contrib.auth.models import User

from .serializers import UserSerializer

from projects.permissions import IsProjectAdmin


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

        # Se o serializer retornar uma tupla, pegamos apenas o primeiro item
        if isinstance(user, tuple):
            user = user[0]

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def perform_create(self, serializer):

        return serializer.save(self.request)


# Classe para visualizar, atualizar e deletar um usuário específico
class UserRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]
    lookup_field = "pk"  # Mantendo a consistência com os padrões Django

        user = serializer.save(self.request)
        return user



class UserDetail(RetrieveDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated & IsAdminUser]
    lookup_field = 'id'

