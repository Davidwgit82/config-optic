from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from utils.enums import PaymentGateway, PaymentStatus

from orders.models import Order


class Payment(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    cart_id = models.IntegerField(null=True, blank=True)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=30, blank=True)
    guest_name = models.CharField(max_length=30, blank=True)

    # Référence renvoyée par GeniusPay (ex: MTX-A1B2C3D4E5)
    reference = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
    )

    # ID interne GeniusPay (champ "id" de la réponse)
    external_id = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
    )

    amount = models.DecimalField(max_digits=10, decimal_places=0)
    fees = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)

    currency = models.CharField(max_length=3, default="XOF")

    gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )

    payment_url = models.URLField(max_length=500, blank=True)
    environment = models.CharField(max_length=10, blank=True)  # sandbox / live

    raw_response = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement {self.reference} - {self.get_status_display()}"