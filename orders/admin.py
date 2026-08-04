from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    """Permet de gérer directement les articles depuis la fiche Commande."""

    model = OrderItem
    extra = 1
    autocomplete_fields = ["product"]
    readonly_fields = ("subtotal_display", "created_at", "updated_at")
    fields = (
        "product",
        "product_name",
        "product_sku",
        "unit_price",
        "quantity",
        "subtotal_display",
    )

    @admin.display(description=_("Sous-total"))
    def subtotal_display(self, obj):
        if obj.pk:
            return f"{obj.subtotal:,.0f} FCFA".replace(",", " ")
        return "-"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Configuration du back-office pour les Commandes."""

    inlines = [OrderItemInline]

    list_display = (
        "reference",
        "user",
        "status_badge",
        "get_total_items",
        "get_total_amount",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "reference",
        "user__phone",
        "user__first_name",
        "user__last_name",
        "user__email",
    )
    autocomplete_fields = ["user"]
    readonly_fields = (
        "reference",
        "get_total_amount",
        "get_total_items",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("reference", "user", "status")}),
        (
            _("Récapitulatif"),
            {"fields": ("get_total_items", "get_total_amount")},
        ),
        (
            _("Métadonnées"),
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    def get_queryset(self, request):
        # Optimisation SQL : charge les items d'un coup pour éviter N+1 requêtes sur total/total_items
        return super().get_queryset(request).prefetch_related("items")

    # --- Colonnes personnalisées & Badges ---

    @admin.display(description=_("Statut"), ordering="status")
    def status_badge(self, obj):
        # Stylisation dynamique selon le statut (ajustez les couleurs si besoin)
        colors = {
            "PENDING": "#ffc107",  # Jaune
            "CONFIRMED": "#17a2b8",  # Bleu clair
            "PROCESSING": "#007bff",  # Bleu
            "SHIPPED": "#6f42c1",  # Violet
            "DELIVERED": "#28a745",  # Vert
            "CANCELLED": "#dc3545",  # Rouge
        }
        color = colors.get(obj.status, "#6c757d")
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; '
            'font-weight: bold; border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description=_("Total"))
    def get_total_amount(self, obj):
        return f"{obj.total:,.0f} FCFA".replace(",", " ")

    @admin.display(description=_("Nb Articles"))
    def get_total_items(self, obj):
        return obj.total_items


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Configuration de consultation individuelle des articles de commande."""

    list_display = (
        "order",
        "product_name",
        "product_sku",
        "unit_price",
        "quantity",
        "get_subtotal",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = (
        "product_name",
        "product_sku",
        "order__reference",
    )
    autocomplete_fields = ["order", "product"]
    readonly_fields = ("subtotal", "created_at", "updated_at")

    @admin.display(description=_("Sous-total"))
    def get_subtotal(self, obj):
        return f"{obj.subtotal:,.0f} FCFA".replace(",", " ")