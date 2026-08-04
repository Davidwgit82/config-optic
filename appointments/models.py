from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from utils.enums import AppointmentStatus, WeekDay
from utils.mixins import NamedModel, TimeMixin
from utils.validators import IvoryCoastPhoneValidator


class AppointmentReason(NamedModel):
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Motif de rendez-vous"
        verbose_name_plural = "Motifs de rendez-vous"

    def __str__(self):
        return self.name


class BusinessHour(TimeMixin):
    day_of_week = models.CharField(
        "Jour",
        max_length=10,
        choices=WeekDay.choices,
        db_index=True,
    )
    open_time = models.TimeField("Heure d'ouverture")
    close_time = models.TimeField("Heure de fermeture")
    is_closed = models.BooleanField("Fermé", default=False)
    reason = models.TextField("Motif de fermeture", blank=True, null=True)

    class Meta:
        ordering = ["day_of_week", "open_time"]
        verbose_name = "Horaire d'ouverture"
        verbose_name_plural = "Horaires d'ouverture"
        constraints = [
            models.UniqueConstraint(
                fields=["day_of_week", "open_time", "close_time"],
                name="unique_business_hour",
            )
        ]

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.open_time.strftime('%H:%M')} - {self.close_time.strftime('%H:%M')}"

    def clean(self):
        super().clean()
        if not self.is_closed and self.open_time >= self.close_time:
            raise ValidationError("L'heure de fermeture doit être supérieure à l'heure d'ouverture.")
        if self.is_closed and not self.reason:
            raise ValidationError({"reason": "Veuillez indiquer le motif de fermeture."})


class Appointment(TimeMixin):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    guest_name = models.CharField("Nom complet", max_length=150, blank=True)
    guest_phone = models.CharField(
        "Téléphone",
        max_length=20,
        blank=True,
        validators=[IvoryCoastPhoneValidator()],
    )
    motif = models.ForeignKey(
        AppointmentReason,
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    appointment_date = models.DateField("Date", db_index=True)
    appointment_time = models.TimeField("Heure", db_index=True)
    notes = models.TextField("Notes", blank=True)
    status = models.CharField(
        "Statut",
        max_length=15,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.PENDING,
        db_index=True,
    )

    class Meta:
        ordering = ["appointment_date", "appointment_time"]
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        constraints = [
            # Empeche de réserver deux RDV actifs au même moment
            models.UniqueConstraint(
                fields=["appointment_date", "appointment_time"],
                condition=~models.Q(status=AppointmentStatus.CANCELLED),
                name="unique_active_appointment_slot",
            )
        ]

    def __str__(self):
        patient_str = self.patient.get_full_name() if self.patient else self.guest_name
        return f"{patient_str} - {self.appointment_date} {self.appointment_time.strftime('%H:%M')}"

    def clean(self):
        super().clean()
        today = timezone.localdate()

        # Validation de la date minimale
        if self.appointment_date < today:
            raise ValidationError({"appointment_date": "La date du rendez-vous ne peut pas être passée."})

        # Validation Guest
        if self.patient is None:
            if not self.guest_name:
                raise ValidationError({"guest_name": "Le nom est obligatoire."})
            if not self.guest_phone:
                raise ValidationError({"guest_phone": "Le téléphone est obligatoire."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)