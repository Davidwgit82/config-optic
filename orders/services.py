from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Order, OrderItem
from catalog.models import Product
from cart.models import Cart
from users.models import User


class OrderService:

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        cart: Cart,
        user: Optional[User] = None,
        guest_email: Optional[str] = None,
        guest_phone: Optional[str] = None,
    ) -> Order:
        """
        Convertit un panier en commande (utilisateur connecté ou invité)
        et réajuste les stocks de manière atomique.
        """
        # 1. Validation du panier et des identifiants
        if cart.is_empty:
            raise ValidationError("Votre panier est vide.")

        if not user and not guest_email:
            raise ValidationError(
                "Un utilisateur connecté ou un email invité est requis pour commander."
            )

        # 2. Verrouillage BDD pessimiste sur tous les produits du panier
        cart_items = list(cart.items.select_related("product").all())
        product_ids = [item.product_id for item in cart_items]

        # On verrouille en BDD les produits concernés
        locked_products = Product.objects.select_for_update().filter(id__in=product_ids)
        products_map = {p.id: p for p in locked_products}

        # 3. Validation préalable des stocks et statut des produits
        products_to_update = []
        order_items_data = []

        for item in cart_items:
            product = products_map.get(item.product_id)

            if not product or not product.is_active:
                raise ValidationError(
                    f"Le produit '{item.product.name}' n'est plus disponible."
                )

            if product.stock < item.quantity:
                raise ValidationError(
                    f"Stock insuffisant pour le produit '{product.name}' (Disponible : {product.stock})."
                )

            # Préparation de la mise à jour de stock
            product.stock -= item.quantity
            products_to_update.append(product)

            # Calcul du prix au moment de la commande
            unit_price = product.promo_price if getattr(product, "is_on_sale", False) else product.price

            order_items_data.append({
                "product": product,
                "product_name": product.name,
                "product_sku": product.sku,
                "unit_price": unit_price,
                "quantity": item.quantity,
            })

        # 4. Création de la commande
        order = Order.objects.create(
            user=user if (user and user.is_authenticated) else None,
            guest_email=guest_email if not (user and user.is_authenticated) else None,
            guest_phone=guest_phone if not (user and user.is_authenticated) else None,
        )

        # 5. Création groupée des OrderItems
        order_items_to_create = [
            OrderItem(
                order=order,
                product=data["product"],
                product_name=data["product_name"],
                product_sku=data["product_sku"],
                unit_price=data["unit_price"],
                quantity=data["quantity"],
            )
            for data in order_items_data
        ]
        OrderItem.objects.bulk_create(order_items_to_create)

        # 6. Mise à jour groupée des stocks (1 seule requête SQL UPDATE)
        Product.objects.bulk_update(products_to_update, fields=["stock"])

        # 7. Vider le panier
        cart.items.all().delete()

        return order

    @staticmethod
    @transaction.atomic
    def cancel_order(order: Order) -> Order:
        """
        Annule une commande et réincrémente les stocks des produits de manière optimisée.
        """
        if order.status == "CANCELLED":
            raise ValidationError("Cette commande est déjà annulée.")

        items = list(order.items.select_related("product").all())
        product_ids = [item.product_id for item in items if item.product_id]

        # Verrouillage des produits à réincrémenter
        locked_products = Product.objects.select_for_update().filter(id__in=product_ids)
        products_map = {p.id: p for p in locked_products}

        products_to_update = []
        for item in items:
            if item.product_id and item.product_id in products_map:
                product = products_map[item.product_id]
                product.stock += item.quantity
                products_to_update.append(product)

        if products_to_update:
            Product.objects.bulk_update(products_to_update, fields=["stock"])

        order.status = "CANCELLED"
        order.save(update_fields=["status"])
        return order