from django.core.exceptions import ValidationError
from django.db import models

from utils.functions import generate_sku
from django.urls import reverse

from utils.mixins import AutoSlugMixin, NamedModel, TimeMixin
from utils.enums import Gender


class Category(NamedModel):

    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children", null=True, blank=True
    )

    is_active = models.BooleanField(default=True, verbose_name="Est actif ?", db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"


class Brand(NamedModel):

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
        verbose_name = "Marque"
        verbose_name_plural = "Marques"


class Product(AutoSlugMixin, TimeMixin):
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", db_index=True
    )

    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )

    color = models.CharField("Couleur", max_length=100, blank=True, null=True, default=None, db_index=True)

    gender = models.CharField(
        "Genre",
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNISEX,
        db_index=True
    )

    """ base fields """
    name = models.CharField(max_length=100, verbose_name="Nom")
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Prix")
    promo_price = models.DecimalField(
        max_digits=10, decimal_places=0, verbose_name="En Promo", blank=True, null=True
    )
    description = models.TextField(blank=True, default="")
    sku = models.CharField(
        max_length=8, unique=True, editable=False, db_index=True, verbose_name="SKU"
    )
    stock = models.PositiveIntegerField(default=0)

    is_active = models.BooleanField(
        default=True, verbose_name="Ce produit est-il actif ?",
        db_index=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["price"]),
        ]

        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    @property
    def est_actif(self):
        return self.is_active and self.stock > 0 and self.price

    def __str__(self):
        cat = self.category.name if self.category else "Category"
        return f"{self.name} - {cat} - {self.get_gender_display()}"

    def get_absolute_url(self):
        return reverse('catalog:product-detail', kwargs={'slug': self.slug})

    def clean(self):
        super().clean()

        if (
            self.promo_price is not None
            and self.price is not None
            and self.promo_price >= self.price
        ):
            raise ValidationError(
                {
                    "promo_price": (
                        "Le prix promotionnel doit être inférieur au prix normal."
                    )
                }
            )


    def save(self, *args, **kwargs):
            self.full_clean()
    
            if not self.sku:
                while True:
                    base_sku = generate_sku()
                    if not self.__class__.objects.filter(sku=base_sku).exists():
                        self.sku = base_sku
                        break
    
            super().save(*args, **kwargs)

    @property
    def is_on_sale(self):
        return self.promo_price is not None and self.promo_price < self.price


class ProductImage(TimeMixin):
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="images",
    )
    file = models.ImageField("Image", upload_to="products/%Y/%m/")
    is_primary = models.BooleanField(
        "Image principale",
        default=False,
        help_text="Première image affichée.",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Image produit"
        verbose_name_plural = "Images produit"
        constraints = [
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_primary=True),
                name="unique_primary_image_per_product",
            )
        ]

    def __str__(self):
        return f"Image de {self.product.name}"

    def clean(self):
        super().clean()

        if self.is_primary and self.product_id:
            exists = ProductImage.objects.filter(
                product_id=self.product_id,
                is_primary=True,
            ).exclude(pk=self.pk)

            if exists.exists():
                raise ValidationError(
                    "Une seule image principale est autorisée par produit."
                )

    def save(self, *args, **kwargs):
        # Si c'est la toute première image du produit, on la passe automatiquement en principale
        if self.pk is None and self.product_id and not self.product.images.exists():
            self.is_primary = True

        self.full_clean()
        super().save(*args, **kwargs)