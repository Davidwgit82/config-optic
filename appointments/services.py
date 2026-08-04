from datetime import datetime, timedelta, time
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from utils.enums import AppointmentStatus, WeekDay
from .models import Appointment, BusinessHour, AppointmentReason


class AppointmentService:

    SLOT_DURATION_MINUTES = 30

    @classmethod
    def get_available_slots(cls, target_date) -> list[str]:
        """
        Génère la liste des créneaux de 30 min libres pour une date donnée (HH:MM).
        """
        if target_date < timezone.localdate():
            return []

        # Convertir le jour Python (0=Lundi, 6=Dimanche) vers l'enum WeekDay
        weekday_map = {
            0: WeekDay.MONDAY, 1: WeekDay.TUESDAY, 2: WeekDay.WEDNESDAY,
            3: WeekDay.THURSDAY, 4: WeekDay.FRIDAY, 5: WeekDay.SATURDAY, 6: WeekDay.SUNDAY
        }
        day_enum = weekday_map[target_date.weekday()]

        # Vérifier si l'établissement est ouvert ce jour-là
        business_hours = BusinessHour.objects.filter(day_of_week=day_enum, is_closed=False)
        if not business_hours.exists():
            return []

        # Récupérer les RDV déjà occupés (non annulés)
        taken_slots = set(
            Appointment.objects.filter(
                appointment_date=target_date
            ).exclude(
                status=AppointmentStatus.CANCELLED
            ).values_list("appointment_time", flat=True)
        )

        available_slots = []
        now = timezone.localtime()

        for bh in business_hours:
            current_dt = datetime.combine(target_date, bh.open_time)
            end_dt = datetime.combine(target_date, bh.close_time)

            while current_dt + timedelta(minutes=cls.SLOT_DURATION_MINUTES) <= end_dt:
                slot_time = current_dt.time()
                
                # Ignorer les créneaux déjà occupés ou déjà passés si c'est aujourd'hui
                is_past = (target_date == now.date() and slot_time <= now.time())
                
                if slot_time not in taken_slots and not is_past:
                    available_slots.append(slot_time.strftime("%H:%M"))

                current_dt += timedelta(minutes=cls.SLOT_DURATION_MINUTES)

        return available_slots

    @classmethod
    @transaction.atomic
    def book_appointment(cls, user, data: dict) -> Appointment:
        """
        Crée un rendez-vous après toutes les vérifications d'usage.
        """
        motif_id = data.get("motif_id")

        # 1. Validation de l'existence et de l'état actif du motif
        try:
            motif = AppointmentReason.objects.get(id=motif_id, is_active=True)
        except AppointmentReason.DoesNotExist:
            raise ValidationError({"motif_id": "Motif de rendez-vous invalide ou inactif."})

        # 2. Validation du créneau dans la grille horaire disponible
        target_date = data["appointment_date"]
        target_time = data["appointment_time"]
        available_slots = cls.get_available_slots(target_date)
        formatted_time = target_time.strftime("%H:%M")

        if formatted_time not in available_slots:
            raise ValidationError({"appointment_time": "Ce créneau horaire n'est pas disponible ou est invalide."})

        # 3. Instanciation du rendez-vous
        appointment = Appointment(
            patient=user if user and user.is_authenticated else None,
            guest_name=data.get("guest_name", ""),
            guest_phone=data.get("guest_phone", ""),
            motif=motif,
            appointment_date=target_date,
            appointment_time=target_time,
            notes=data.get("notes", "")
        )
        appointment.save()
        return appointment

    @staticmethod
    def update_completed_appointments():
        """
        Automatisable via Tâche Celery / CRON : Passe en COMPLETED les RDV confirmés expirés.
        """
        now = timezone.localtime()
        Appointment.objects.filter(
            status=AppointmentStatus.CONFIRMED,
            appointment_date__lte=now.date(),
            appointment_time__lt=now.time()
        ).update(status=AppointmentStatus.COMPLETED)