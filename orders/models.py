import uuid

from django.db import models

from utils.mixins import TimeMixin
from utils.enums import OrderStatus
from utils.functions import generate_order_reference
from django.core.exceptions import ValidationError
from django.conf import settings
from catalog.models import Product


class Order(TimeMixin):
    reference = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        db_index=True,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )

    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

    def __str__(self):
        return f"Commande {self.reference}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


    def save(self, *args, **kwargs):
        if not self.reference:
            while True:
                reference = generate_order_reference()

                if not Order.objects.filter(reference=reference).exists():
                    self.reference = reference
                    break

        self.full_clean()
        super().save(*args, **kwargs)


class OrderItem(TimeMixin):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="order_items",
    )

    product_name = models.CharField(max_length=100)
    product_sku = models.CharField(max_length=8)

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
    )

    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Article de commande"
        verbose_name_plural = "Articles de commande"

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    def clean(self):
        super().clean()

        if self.quantity < 1:
            raise ValidationError({
                "quantity": "La quantité doit être supérieure à zéro."
            })

    def save(self, *args, **kwargs):
        if not self.product_name:
            self.product_name = self.product.name

        if not self.product_sku:
            self.product_sku = self.product.sku

        if not self.unit_price:
            self.unit_price = (
                self.product.promo_price
                if self.product.is_on_sale
                else self.product.price
            )

        self.full_clean()
        super().save(*args, **kwargs)
