from django.core.exceptions import ValidationError
from django.db import models

from utils.functions import generate_sku
from django.urls import reverse

from utils.mixins import AutoSlugMixin, NamedModel, TimeMixin


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
        return f"{self.name} - {cat}"

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
        Product, on_delete=models.CASCADE, related_name="images"
    )

    file = models.ImageField("Image", upload_to="products/%Y/%m/")
    is_primary = models.BooleanField(default=False, verbose_name="Image principale", help_text="Premiere image affichée.")

    class Meta:
        ordering = ["id"]

        verbose_name = "Image produit"
        verbose_name_plural = "Images produit"

    def __str__(self):
        return f"Image de {self.product.name}"


    def clean(self):
        super().clean()


        if self.is_primary:
            exists = ProductImage.objects.filter(
                product=self.product,
                is_primary=True,
            ).exclude(pk=self.pk)

            if exists.exists():
                raise ValidationError(
                    "Une seule image principale est autorisée par produit."
                )

    def save(self, *args, **kwargs):

        self.full_clean()

        if self.pk is None and not self.product.images.exists():
            self.is_primary = True

        super().save(*args, **kwargs)
