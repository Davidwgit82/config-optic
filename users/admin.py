from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User, AdminUser, ClientUser, Prescription


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0
    readonly_fields = ("reference", "created_at", "updated_at")
    fields = ("reference", "file", "created_at")


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Configuration de base pour le modèle User personnalisé."""

    inlines = [PrescriptionInline]

    # Paramètres de liste
    list_display = (
        "phone",
        "first_name",
        "last_name",
        "email",
        "country",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "country", "created_at")
    search_fields = ("phone", "first_name", "last_name", "email")
    ordering = ("-created_at",)

    # Adaptations pour l'utilisation de 'phone' comme USERNAME_FIELD
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (
            _("Informations personnelles"),
            {"fields": ("first_name", "last_name", "email", "country", "latitude", "longitude")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            _("Dates importantes"),
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    readonly_fields = ("last_login", "date_joined", "created_at", "updated_at")

    # Options de la carte GeoDjango (OpenStreetMap)
    # gis_widget_kwargs = {
    #     "attrs": {
    #         "default_zoom": 12,
    #         "default_lon": -3.9962,  # Coordonnées par défaut (ex: Abidjan, Côte d'Ivoire)
    #         "default_lat": 5.3600,
    #     }
    # }


@admin.register(AdminUser)
class AdminUserAdmin(CustomUserAdmin):
    """Admin dédié aux Administrateurs / Staff."""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)


@admin.register(ClientUser)
class ClientUserAdmin(CustomUserAdmin):
    """Admin dédié aux Utilisateurs / Clients simples."""

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    """Configuration de l'administration des Ordonnances."""

    list_display = ("reference", "user", "file", "created_at")
    list_filter = ("created_at",)
    search_fields = (
        "reference",
        "user__phone",
        "user__first_name",
        "user__last_name",
    )
    readonly_fields = ("reference", "created_at", "updated_at")
    autocomplete_fields = ["user"]
    ordering = ("-created_at",)