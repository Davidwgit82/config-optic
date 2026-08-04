from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .serializers import UserRegisterSerializer, UserProfileSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegisterSerializer
        return UserProfileSerializer

    def get_permissions(self):
        if self.action == "create":
            # Inscription ouverte à tous
            return [permissions.AllowAny()]
        # Tout le reste nécessite d'être authentifié
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["get", "put", "patch"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Point d'accès sécurisé pour lire et mettre à jour le profil de l'utilisateur connecté.
        Endpoint: /api/v1/users/me/
        """
        user = request.user

        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

        # PUT / PATCH
        partial = request.method == "PATCH"
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)