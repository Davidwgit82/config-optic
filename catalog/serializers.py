from rest_framework import serializers
from .models import Category, Brand, Product, ProductImage


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ("id", "name")


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "file", "is_primary")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "parent", "is_active")


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name", read_only=True)
    brand = serializers.CharField(source="brand.name", read_only=True, default=None)
    primary_image = serializers.SerializerMethodField()
    is_on_sale = serializers.BooleanField(read_only=True)

    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "price",
            "promo_price",
            "is_on_sale",
            "category",
            "brand",
            "stock",
            "primary_image",
            "images",
        )

    def get_primary_image(self, obj):
        images = getattr(obj, "prefetched_images", obj.images.all())
        primary = next((img for img in images if img.is_primary), None) or (images[0] if images else None)
        if primary:
            request = self.context.get("request")
            return request.build_absolute_uri(primary.file.url) if request else primary.file.url
        return None


    def get_images(self, obj):
        request = self.context.get("request")
        images = getattr(obj, "prefetched_images", obj.images.all())
        urls = [img.file.url for img in images]
        if request:
            return [request.build_absolute_uri(u) for u in urls]
        return urls


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    est_actif = serializers.BooleanField(read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "sku",
            "description",
            "price",
            "promo_price",
            "stock",
            "est_actif",
            "is_on_sale",
            "category",
            "brand",
            "images",
            "created_at",
        )


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "category",
            "brand",
            "name",
            "price",
            "promo_price",
            "description",
            "stock",
            "is_active",
        )

    def validate(self, attrs):
        # DRF exécute cette validation avant la sauvegarde
        price = attrs.get("price", getattr(self.instance, "price", None))
        promo_price = attrs.get("promo_price", getattr(self.instance, "promo_price", None))

        if promo_price is not None and price is not None and promo_price >= price:
            raise serializers.ValidationError(
                {"promo_price": "Le prix promotionnel doit être strictement inférieur au prix normal."}
            )
        return attrs

