from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Autorise la lecture (GET, HEAD, OPTIONS) à tout le monde.
    Exige d'être 'is_staff' pour les actions d'écriture (POST, PUT, PATCH, DELETE).
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)