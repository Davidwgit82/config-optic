from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserViewSet
from .auth_views import CustomTokenObtainPairView

app_name = "users"

router = SimpleRouter()
router.register(r"", UserViewSet, basename="user")

urlpatterns = [
    # Routes d'authentification JWT
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Routes de gestion d'utilisateur (/ et /me/)
    path("", include(router.urls)),
]