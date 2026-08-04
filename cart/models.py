from django.db import models

from catalog.models import Product
from utils.mixins import TimeMixin

from django.conf import settings


class Cart(TimeMixin):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        null=True,
        blank=True,
    )

    session_key = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
    )

    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"

    def __str__(self):
        return self.user.get_full_name() if self.user else self.session_key

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def is_empty(self):
        return not self.items.exists()


class CartItem(TimeMixin):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Article du panier"
        verbose_name_plural = "Articles du panier"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"],
                name="unique_product_per_cart",
            )
        ]

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    @property
    def unit_price(self):
        return (
            self.product.promo_price
            if self.product.is_on_sale
            else self.product.price
        )

    @property
    def subtotal(self):
        return self.unit_price * self.quantity