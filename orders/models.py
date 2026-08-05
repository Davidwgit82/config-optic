import uuid
from django.db import models, IntegrityError
from django.core.exceptions import ValidationError
from django.conf import settings
from utils.mixins import TimeMixin
from utils.enums import OrderStatus
from utils.functions import generate_order_reference
from catalog.models import Product


class Order(TimeMixin):
    reference = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        db_index=True,
    )

    # Relation utilisateur facultative (Guest Checkout)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )

    # Informations obligatoires pour le Guest Checkout
    guest_email = models.EmailField(blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)

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
    def email(self):
        """Retourne l'email du client (inscrit ou invité)."""
        return self.user.email if self.user else self.guest_email

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    def clean(self):
        super().clean()
        # Validation métier : une commande doit avoir soit un user, soit un guest_email
        if not self.user and not self.guest_email:
            raise ValidationError(
                "Une commande doit être liée à un utilisateur ou contenir un email invité."
            )

    def save(self, *args, **kwargs):
        if not self.reference:
            # Essais successifs de génération sans blocage infini
            for _ in range(5):
                ref = generate_order_reference()
                if not Order.objects.filter(reference=ref).exists():
                    self.reference = ref
                    break
            if not self.reference:
                raise ValidationError("Impossible de générer une référence unique.")

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
        if not self.product_name and self.product:
            self.product_name = self.product.name

        if not self.product_sku and self.product:
            self.product_sku = self.product.sku

        if self.unit_price is None and self.product:
            is_on_sale = getattr(self.product, 'is_on_sale', False)
            self.unit_price = (
                self.product.promo_price if is_on_sale else self.product.price
            )

        self.full_clean()
        super().save(*args, **kwargs)