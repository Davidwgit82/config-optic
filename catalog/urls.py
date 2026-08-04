from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import ProductViewSet

app_name = "catalog"

# SimpleRouter pour des URLs REST propres
router = SimpleRouter()

# Route principale des produits
# Génère :
# - GET /                      -> Liste des produits (ProductListSerializer)
# - POST /                     -> Créer un produit (ProductWriteSerializer) - Admin
# - GET /{slug}/               -> Détail d'un produit (ProductDetailSerializer)
# - PUT / PATCH /{slug}/       -> Modifier un produit - Admin
# - DELETE /{slug}/            -> Supprimer un produit - Admin
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    path("", include(router.urls)),
]