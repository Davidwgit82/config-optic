from django.contrib import admin
from django.utils.html import format_html
from utils.enums import AppointmentStatus
from .models import Appointment, AppointmentReason, BusinessHour


@admin.register(AppointmentReason)
class AppointmentReasonAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active",)
    ordering = ("name",)


@admin.register(BusinessHour)
class BusinessHourAdmin(admin.ModelAdmin):
    list_display = (
        "day_of_week",
        "open_time",
        "close_time",
        "is_closed",
        "reason",
    )
    list_filter = ("day_of_week", "is_closed")
    search_fields = ("reason",)
    list_editable = ("is_closed",)
    ordering = ("day_of_week", "open_time")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "get_patient_display",
        "get_phone_display",
        "motif",
        "appointment_date",
        "appointment_time",
        "status",
        "created_at",
    )
    list_filter = ("status", "appointment_date", "motif")
    list_editable = ("status",)
    
    search_fields = (
        "guest_name",
        "guest_phone",
        "patient__first_name",
        "patient__last_name",
        "patient__email",
        "notes",
    )
    date_hierarchy = "appointment_date"
    autocomplete_fields = ["patient", "motif"]
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            "Informations du Patient",
            {
                "fields": (
                    "patient",
                    ("guest_name", "guest_phone"),
                ),
            },
        ),
        (
            "Détails du Rendez-vous",
            {
                "fields": (
                    "motif",
                    ("appointment_date", "appointment_time"),
                    "status",
                    "notes",
                ),
            },
        ),
        (
            "Métadonnées",
            {
                "classes": ("collapse",),
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Patient / Invité")
    def get_patient_display(self, obj):
        if obj.patient:
            return f"{obj.patient.get_full_name()} (Inscrit)"
        return f"{obj.guest_name} (Invité)"

    @admin.display(description="Téléphone")
    def get_phone_display(self, obj):
        if obj.patient and hasattr(obj.patient, "phone"):
            return obj.patient.phone
        return obj.guest_phone or "-"

    @admin.display(description="Statut")
    def status_badge(self, obj):
        colors = {
            AppointmentStatus.PENDING: "#d97706",
            AppointmentStatus.CONFIRMED: "#2563eb",
            AppointmentStatus.COMPLETED: "#16a34a",
            AppointmentStatus.CANCELLED: "#dc2626",
        }
        color = colors.get(obj.status, "#4b5563")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )