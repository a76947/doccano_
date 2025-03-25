from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer as DefaultRegisterSerializer


class UserSerializer(serializers.ModelSerializer):
    # Para atualizar senha via PATCH/PUT, precisamos deste campo.
    # Ele é write_only para não aparecer em GET.
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = get_user_model()

        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "is_superuser",
            "is_staff",
            "email",
            "last_login",
            "password"
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

        fields = ("id", "username", "first_name", "last_name", "is_superuser", "is_staff", "email", "last_login")




class CustomRegisterSerializer(DefaultRegisterSerializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def custom_signup(self, request, user):

        user.first_name = self.validated_data.get("first_name", "")
        user.last_name = self.validated_data.get("last_name", "")
        user.save()

        user.first_name = self.validated_data.get('first_name', '')
        user.last_name = self.validated_data.get('last_name', '')
        user.save()

