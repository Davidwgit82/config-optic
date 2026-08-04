from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Order, OrderItem
from catalog.models import Product
from cart.models import Cart

from users.models import User


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user: User) -> Order:
        """Convertit le panier d'un utilisateur en commande et vide le panier."""
        try:
            cart = Cart.objects.prefetch_related("items__product").get(user=user)
        except Cart.DoesNotExist:
            raise ValidationError("Aucun panier trouvé.")

        if cart.is_empty:
            raise ValidationError("Votre panier est vide.")

        # 1. Verrouillage BDD pessimiste sur les produits
        product_ids = [item.product_id for item in cart.items.all()]
        products = Product.objects.select_for_update().filter(id__in=product_ids, is_active=True)
        products_map = {p.id: p for p in products}

        order = Order.objects.create(user=user)
        order_items_to_create = []

        # 2. Validation stricte des stocks et prix
        for item in cart.items.all():
            product = products_map.get(item.product_id)
            if not product or product.stock < item.quantity:
                raise ValidationError(f"Stock insuffisant pour le produit '{item.product.name}'.")

            product.stock -= item.quantity
            product.save(update_fields=["stock"])

            unit_price = product.promo_price if product.is_on_sale else product.price

            order_items_to_create.append(
                OrderItem(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    unit_price=unit_price,
                    quantity=item.quantity
                )
            )

        OrderItem.objects.bulk_create(order_items_to_create)

        # 3. Vider le panier
        cart.items.all().delete()

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order) -> Order:
        """
        Annule une commande et réincrémente les stocks.
        """
        if order.status == "CANCELLED":
            raise ValidationError("Cette commande est déjà annulée.")

        # Réincrémentation des stocks avec verrou BDD
        for item in order.items.select_related("product").select_for_update():
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=["stock"])

        order.status = "CANCELLED"
        order.save(update_fields=["status"])
        return order