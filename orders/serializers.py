from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemReadSerializer(serializers.ModelSerializer):
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "product_name",
            "product_sku",
            "unit_price",
            "quantity",
            "subtotal",
        )


class OrderReadSerializer(serializers.ModelSerializer):
    items = OrderItemReadSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    email = serializers.ReadOnlyField()  # Propriété du modèle qui renvoie l'email user ou guest

    class Meta:
        model = Order
        fields = (
            "id",
            "reference",
            "user",
            "guest_email",
            "guest_phone",
            "email",
            "status",
            "total",
            "total_items",
            "items",
            "created_at",
        )


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer pour la création de commande.
    Les articles sont extraits directement du panier en BDD par le service.
    """
    guest_email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    guest_phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        # Si l'utilisateur n'est pas authentifié, l'email invité devient obligatoire
        is_authenticated = user and user.is_authenticated
        guest_email = attrs.get("guest_email")

        if not is_authenticated and not guest_email:
            raise serializers.ValidationError({
                "guest_email": "L'adresse email est obligatoire pour passer une commande sans compte."
            })

        return attrs