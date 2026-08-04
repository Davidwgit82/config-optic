from rest_framework import serializers
from .models import Appointment, AppointmentReason


class AppointmentReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentReason
        fields = ("id", "name")


class AppointmentReadSerializer(serializers.ModelSerializer):
    motif = AppointmentReasonSerializer(read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = (
            "id",
            "patient_name",
            "guest_name",
            "guest_phone",
            "motif",
            "appointment_date",
            "appointment_time",
            "notes",
            "status",
            "created_at",
        )

    def get_patient_name(self, obj):
        return obj.patient.get_full_name() if obj.patient else obj.guest_name


class AppointmentCreateSerializer(serializers.Serializer):
    motif_id = serializers.IntegerField()
    appointment_date = serializers.DateField()
    appointment_time = serializers.TimeField(format="%H:%M")
    guest_name = serializers.CharField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)