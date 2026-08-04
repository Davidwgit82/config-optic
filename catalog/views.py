from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.http import require_POST
# from .services import ProductService
# import json

# Create your views here.

""" crud pour admin """
"""@require_POST
def api_create_product(request):
    data = json.loads(request.body)
    
    # Appel direct de la méthode statique du service
    product = ProductService.create_product_with_image(
        name=data['name'],
        category_id=data['category_id'],
        price=data['price'],
        image_urls=data.get('images', [])
    )
    
    return JsonResponse({
        "status": "success", 
        "product_id": product.id
    }, status=201)"""


from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from .models import Product, ProductImage
from utils.permissions import IsAdminOrReadOnly
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductWriteSerializer,
)


class ProductViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"  # Utilise le slug dans les URLs à la place de l'ID (e-commerce SEO)
    permission_classes = [IsAdminOrReadOnly]
    
    # Filtres, Recherche et Tri
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "brand", "is_active"]
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["price", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """
        Optimisation critique des requêtes SQL (Anti N+1).
        - select_related pour les clés étrangères simples (1-1 ou N-1).
        - prefetch_related pour les relations M-N ou 1-N (Images).
        """
        queryset = Product.objects.select_related("category", "brand")

        # Pour la liste, on ne charge que les images indispensables (prefetch)
        images_prefetch = Prefetch(
            "images",
            queryset=ProductImage.objects.only("id", "product_id", "file", "is_primary"),
            to_attr="prefetched_images"
        )
        
        # Filtre de visibilité : Les non-admins ne voient que les produits actifs
        if not (self.request.user and self.request.user.is_authenticated and self.request.user.is_staff):
            queryset = queryset.filter(is_active=True)

        return queryset.prefetch_related(images_prefetch)

    def get_serializer_class(self):
        """
        Dynamise le Serializer selon l'action.
        """
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "retrieve":
            return ProductDetailSerializer
        # Pour create, update, partial_update
        return ProductWriteSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Gestion de la suppression : Soft Delete vs Hard Delete.
        Par défaut ici, une suppression définitive (DELETE) est exécutée,
        seul un Admin (is_staff) peut atteindre ce code grâce à IsAdminOrReadOnly.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": "Le produit a été supprimé avec succès."},
            status=status.HTTP_204_NO_CONTENT
        )