from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import Order
from .serializers import OrderReadSerializer, OrderCreateSerializer
from .services import OrderService


class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Un utilisateur ne voit QUE ses propres commandes (Sécurité IDOR)
        # Admins (is_staff) voient toutes les commandes
        user = self.request.user
        queryset = Order.objects.all() if user.is_staff else Order.objects.filter(user=user)
        
        # Anti N+1 Query
        return queryset.prefetch_related("items")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # On supprime items_data car le service va chercher le panier tout seul via l'utilisateur
            order = OrderService.create_order_from_cart(user=request.user)
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, "message_dict") else e.messages)

        read_serializer = OrderReadSerializer(order, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """
        Endpoint custom: POST /api/v1/orders/{id}/cancel/
        """
        order = self.get_object()
        try:
            cancelled_order = OrderService.cancel_order(order)
        except DjangoValidationError as e:
            raise DRFValidationError(e.messages)

        serializer = OrderReadSerializer(cancelled_order)
        return Response(serializer.data, status=status.HTTP_200_OK)