from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdmin(BasePermission):
    """
    Permite acesso se o usuário for staff/admin
    OU se for o dono (obj == request.user).
    """

    def has_object_permission(self, request, view, obj):
        # Se for staff/superuser, pode tudo
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Se for GET (ou HEAD, OPTIONS) e quiseres permitir leitura,
        # podes permitir. (Opcional)
        # if request.method in SAFE_METHODS:
        #     return True

        # Caso contrário, só permite se o obj for o mesmo user logado
        return obj == request.user
