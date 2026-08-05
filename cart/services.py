from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.models import Product
from users.models import User

from .models import Cart, CartItem


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
        """Ajoute un produit au panier ou cumule la quantité si déjà présent."""
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise ValidationError("Produit introuvable ou inactif.")

        if product.stock < quantity:
            raise ValidationError(f"Stock insuffisant ({product.stock} disponible(s)).")

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity},
        )

        if not created:
            new_quantity = item.quantity + quantity
            if product.stock < new_quantity:
                raise ValidationError(
                    f"Impossible d'ajouter cette quantité. Stock maximum disponible : {product.stock}."
                )
            item.quantity = new_quantity
            item.save(update_fields=["quantity"])

        return item

    @staticmethod
    def update_item_quantity(cart: Cart, item_id: int, quantity: int) -> CartItem:
        """Met à jour la quantité exacte d'un article du panier avec vérification de stock."""
        try:
            item = CartItem.objects.select_related("product").get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            raise ValidationError("Article introuvable dans le panier.")

        if quantity > item.product.stock:
            raise ValidationError(
                f"La quantité demandée dépasse le stock disponible ({item.product.stock} max)."
            )

        item.quantity = quantity
        item.save(update_fields=["quantity"])
        return item

    @staticmethod
    def remove_from_cart(cart: Cart, item_id: int) -> None:
        """Supprime un article du panier."""
        CartItem.objects.filter(id=item_id, cart=cart).delete()

    @staticmethod
    def clear_cart(cart: Cart) -> None:
        """Vide l'intégralité du panier."""
        cart.items.all().delete()

    @staticmethod
    def merge_session_cart_to_user(session_key: str, user: User) -> None:
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
                    cart=user_cart,
                    product=item.product,
                    defaults={"quantity": item.quantity},
                )
                if not created:
                    new_qty = user_item.quantity + item.quantity
                    # Plafond selon le stock disponible
                    user_item.quantity = min(new_qty, item.product.stock)
                    user_item.save(update_fields=["quantity"])

            guest_cart.delete()