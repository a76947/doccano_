from django.contrib.auth import get_user_model
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    # Para atualizar senha via PATCH/PUT, precisamos deste campo.
    # Ele é write_only para não aparecer em GET.
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
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
