from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from datetime import datetime

from .models import Appointment, AppointmentReason
from .serializers import AppointmentReadSerializer, AppointmentCreateSerializer, AppointmentReasonSerializer
from .services import AppointmentService


class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Appointment.objects.none()
        if user.is_staff:
            return Appointment.objects.all().select_related("motif", "patient")
        return Appointment.objects.filter(patient=user).select_related("motif", "patient")

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        return AppointmentReadSerializer

    @action(detail=False, methods=["get"], url_path="available-slots")
    def available_slots(self, request):
        """GET /api/v1/appointments/available-slots/?date=YYYY-MM-DD"""
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"detail": "Le paramètre 'date' est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "Format date invalide. Utilisez YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        slots = AppointmentService.get_available_slots(target_date)
        return Response({"date": date_str, "available_slots": slots})

    @action(detail=False, methods=["get"], url_path="motifs")
    def active_motifs(self, request):
        """GET /api/v1/appointments/motifs/"""
        motifs = AppointmentReason.objects.filter(is_active=True)
        return Response(AppointmentReasonSerializer(motifs, many=True).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            appointment = AppointmentService.book_appointment(
                user=request.user,
                data=serializer.validated_data
            )
        except DjangoValidationError as e:
            raise DRFValidationError(e.message_dict if hasattr(e, "message_dict") else e.messages)

        return Response(AppointmentReadSerializer(appointment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request, pk=None):
        """POST /api/v1/appointments/{id}/cancel/"""
        appointment = self.get_object()
        if appointment.status == "CANCELLED":
            return Response({"detail": "Ce rendez-vous est déjà annulé."}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = "CANCELLED"
        appointment.save(update_fields=["status"])
        return Response(AppointmentReadSerializer(appointment).data, status=status.HTTP_200_OK)