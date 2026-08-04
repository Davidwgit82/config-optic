from django.contrib import admin
from django.utils.html import format_html

from .models import Brand, Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("preview", "file", "is_primary")
    readonly_fields = ("preview",)

    @admin.display(description="Aperçu")
    def preview(self, obj):
        if obj.pk and obj.file:
            return format_html(
                '<img src="{}" width="80" style="border-radius:6px;" />',
                obj.file.url,
            )
        return "-"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)

    autocomplete_fields = ('parent',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "brand",
        "price",
        "promo_price",
        "stock",
        "is_on_sale",
        "is_active",
    )
    list_display_links = ("name",)
    list_filter = ("category", "brand", "is_active")
    search_fields = ("name", "sku")
    autocomplete_fields = ("category", "brand")
    readonly_fields = ("sku", "slug", "created_at", "updated_at")
    list_select_related = ("category", "brand")
    list_per_page = 25
    inlines = (ProductImageInline,)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "category",
                    "brand",
                    "name",
                    "slug",
                    "description",
                )
            },
        ),
        (
            "Tarification",
            {
                "fields": (
                    "price",
                    "promo_price",
                    "stock",
                )
            },
        ),
        (
            "Informations",
            {
                "fields": (
                    "sku",
                    "is_active",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    @admin.display(boolean=True, description="Promo")
    def is_on_sale(self, obj):
        return obj.is_on_sale


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("preview", "product", "is_primary", "created_at")
    list_filter = ("is_primary",)
    search_fields = ("product__name",)
    autocomplete_fields = ("product",)
    readonly_fields = ("preview", "created_at", "updated_at")

    @admin.display(description="Aperçu")
    def preview(self, obj):
        if obj.file:
            return format_html(
                '<img src="{}" width="80" style="border-radius:6px;" />',
                obj.file.url,
            )
        return "-"