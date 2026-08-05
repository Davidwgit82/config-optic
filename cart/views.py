from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import AddToCartSerializer, CartSerializer, UpdateCartItemSerializer
from .services import CartService


class CartViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]

    def _get_cart(self, request) -> Cart:
        user = request.user if request.user.is_authenticated else None
        session_key = request.headers.get("X-Session-Key") or request.session.session_key

        if not user and not session_key:
            if not request.session.exists(request.session.session_key):
                request.session.create()
            session_key = request.session.session_key

        return CartService.get_or_create_cart(user=user, session_key=session_key)

    def list(self, request):
        """GET /api/v1/cart/ : Récupère le panier en cours"""
        cart = self._get_cart(request)
        serializer = CartSerializer(cart, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="add")
    def add_item(self, request):
        """POST /api/v1/cart/add/ : Ajoute un article"""
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = self._get_cart(request)
        try:
            CartService.add_to_cart(
                cart=cart,
                product_id=serializer.validated_data["product_id"],
                quantity=serializer.validated_data["quantity"],
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)

        # Force la réévaluation des relations et des propriétés calculées (subtotal, total_items)
        cart.refresh_from_db()

        return Response(
            CartSerializer(cart, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["patch", "delete"], url_path="items/(?P<item_id>[^/.]+)")
    def update_or_delete_item(self, request, item_id=None):
        """PATCH/DELETE /api/v1/cart/items/{item_id}/ : Modifie la quantité ou supprime l'article"""
        cart = self._get_cart(request)

        try:
            if request.method == "DELETE":
                CartService.remove_from_cart(cart=cart, item_id=item_id)
            else:  # PATCH
                serializer = UpdateCartItemSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                CartService.update_item_quantity(
                    cart=cart,
                    item_id=item_id,
                    quantity=serializer.validated_data["quantity"],
                )
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)

        # Force le rechargement propre des relations et sous-totaux mis à jour
        cart.refresh_from_db()

        return Response(
            CartSerializer(cart, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )