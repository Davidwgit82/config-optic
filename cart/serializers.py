from rest_framework import serializers
from .models import Cart, CartItem
from catalog.serializers import ProductListSerializer


class CartItemReadSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "unit_price", "subtotal")


class CartSerializer(serializers.ModelSerializer):
    items = CartItemReadSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    total_items = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "total_items", "subtotal", "items")


class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)