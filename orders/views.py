from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError as DRFValidationError, PermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Order
from .serializers import OrderReadSerializer, OrderCreateSerializer
from .services import OrderService
from cart.services import CartService


class OrderViewSet(viewsets.ModelViewSet):
    """
    Gestion des commandes avec support du Guest Checkout (invités)
    et sécurisation des accès utilisateurs/staff.
    """

    def get_permissions(self):
        # Permet aux utilisateurs non connectés de créer une commande (Guest Checkout)
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        # Sécurité : Un utilisateur anonyme ne peut pas lister les commandes
        if not user or not user.is_authenticated:
            return Order.objects.none()

        # Staff voit tout, un client ne voit QUE ses propres commandes
        queryset = Order.objects.all() if user.is_staff else Order.objects.filter(user=user)

        # Optimisation SQL Anti-N+1
        return queryset.prefetch_related("items")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    def create(self, request, *args, **kwargs):
        # 1. Validation de la requête HTTP via le serializer
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # 2. Récupération du panier lié à la requête (User ou Session invité)
        cart = CartService.get_cart_from_request(request)

        user = request.user if request.user.is_authenticated else None

        # 3. Exécution de la transaction métier via le service
        try:
            order = OrderService.create_order_from_cart(
                cart=cart,
                user=user,
                guest_email=serializer.validated_data.get("guest_email"),
                guest_phone=serializer.validated_data.get("guest_phone"),
            )
        except DjangoValidationError as e:
            raise DRFValidationError(
                e.message_dict if hasattr(e, "message_dict") else e.messages
            )

        # 4. Rendu de la réponse
        read_serializer = OrderReadSerializer(order, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Endpoint d'annulation : POST /api/v1/orders/{id}/cancel/
        """
        order = self.get_object()

        # Vérification d'autorisation (seul le propriétaire ou le staff annule)
        if not request.user.is_staff and order.user != request.user:
            raise PermissionDenied("Vous n'êtes pas autorisé à annuler cette commande.")

        try:
            cancelled_order = OrderService.cancel_order(order)
        except DjangoValidationError as e:
            raise DRFValidationError(
                e.message_dict if hasattr(e, "message_dict") else e.messages
            )

        serializer = OrderReadSerializer(cancelled_order, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)