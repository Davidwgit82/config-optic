from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _

class Country(TextChoices):
    CI = "CI", _("Côte d'ivoire"),
    SN = "SN", _("Sénegal"),
    CAM = "CAM", _("Cameroun")

class AppointmentStatus(TextChoices):
    PENDING = "PENDING", "En attente"
    CONFIRMED = "CONFIRMED", "Confirmée"
    CANCELLED = "CANCELLED", "Annulée"
    COMPLETED = "COMPLETED","Terminée"

class OrderStatus(TextChoices):
    PENDING = "PENDING", "En attente"
    PAID = "PAID", "Payée"
    CANCELLED = "CANCELLED", "Annulée"


# class ConsultationType(TextChoices):
#     HOME = "HOME", "A domicile",
#     ON_SITE = "ON_SITE", "Sur place"


class WeekDay(TextChoices):
    MONDAY = "MONDAY", "Lundi"
    TUESDAY = "TUESDAY", "Mardi"
    WEDNESDAY = "WEDNESDAY", "Mercredi"
    THURSDAY = "THURSDAY", "Jeudi"
    FRIDAY = "FRIDAY", "Vendredi"
    SATURDAY = "SATURDAY", "Samedi"
    SUNDAY = "SUNDAY", "Dimanche"


class Gender(TextChoices):
    MEN = "MEN", "Homme"
    WOMEN = "WOMEN", "Femme"
    UNISEX = "UNISEX", "Unisexe"
    KIDS = "KIDS", "Enfant"