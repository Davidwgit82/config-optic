from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Cart, CartItem
from catalog.models import Product
from orders.models import Order, OrderItem

from users.models import User   


class CartService:

    @staticmethod
    def get_or_create_cart(user=None, session_key=None) -> Cart:
        """Récupère ou crée un panier basé sur l'utilisateur ou la session."""
        if user and user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
            return cart
        elif session_key:
            cart, _ = Cart.objects.get_or_create(session_key=session_key)
            return cart
        raise ValidationError("Un utilisateur authentifié ou une clef de session est requis.")

    @staticmethod
    def add_to_cart(cart: Cart, product_id: int, quantity: int = 1) -> CartItem:
        """Ajoute un produit au panier ou met à jour sa quantité."""
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise ValidationError("Produit introuvable ou inactif.")

        if product.stock < quantity:
            raise ValidationError(f"Stock insuffisant ({product.stock} disponibles).")

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            new_quantity = item.quantity + quantity
            if product.stock < new_quantity:
                raise ValidationError(f"Stock insuffisant pour ajouter cet article ({product.stock} max).")
            item.quantity = new_quantity
            item.save(update_fields=["quantity"])

        return item

    @staticmethod
    def merge_session_cart_to_user(session_key: str, user: User):
        """Fusionne le panier invité dans le panier utilisateur lors de la connexion."""
        if not session_key:
            return

        try:
            guest_cart = Cart.objects.get(session_key=session_key)
        except Cart.DoesNotExist:
            return

        user_cart, _ = Cart.objects.get_or_create(user=user)

        with transaction.atomic():
            for item in guest_cart.items.select_related("product"):
                user_item, created = CartItem.objects.get_or_create(
                    cart=user_cart, product=item.product,
                    defaults={"quantity": item.quantity}
                )
                if not created:
                    user_item.quantity += item.quantity
                    # Vérification du stock au moment du merge
                    if user_item.quantity > item.product.stock:
                        user_item.quantity = item.product.stock
                    user_item.save(update_fields=["quantity"])

            guest_cart.delete()