from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from utils.validators import IvoryCoastPhoneValidator
from utils.mixins import TimeMixin
from .managers import CustomUserManager
from utils.enums import Country
from django.db import models 

import uuid

class User(AbstractUser, TimeMixin):
    username = None

    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")

    phone = models.CharField(
        max_length=20,
        validators=[IvoryCoastPhoneValidator()],
        unique=True,
        db_index=True,
        verbose_name="Téléphone"
    )

    email = models.EmailField(blank=True)
    country = models.CharField(max_length=3, choices=Country.choices, default="CI", db_index=True)

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = CustomUserManager()

    USERNAME_FIELD =  "phone"
    REQUIRED_FIELDS = ["first_name"]

    def get_short_name(self):
        return self.first_name

    def __str__(self):
        full_name = self.get_full_name().strip()
        return full_name if full_name else self.phone

    class Meta:
        ordering = ["-created_at"]


class Prescription(TimeMixin):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    reference = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
    )

    file = models.FileField(upload_to="prescriptions/%Y/%m/%d", verbose_name="Ordonnance", validators=[
        FileExtensionValidator(["pdf","jpg","jpeg","png"])
    ])

    class Meta:
        verbose_name = "Ordonnance"
        verbose_name_plural = "Ordonnances"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Ordonnance de {self.user}"


""" dispatch user """
class AdminUser(User):

    class Meta:
        proxy = True
        verbose_name = "Administrateur"
        verbose_name_plural = "Administrateurs"


class ClientUser(User):

    class Meta:
        proxy = True
        verbose_name = "Clients"
        verbose_name_plural = "Clients"

