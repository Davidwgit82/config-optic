from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

import logging

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema

from orders.models import Order
from utils.enums import OrderStatus, PaymentStatus
from .models import Payment
from .serializers import InitiatePaymentSerializer, PaymentResponseSerializer
from .services import GeniusPayClient, GeniusPayError
from .webhook_utils import verify_webhook_signature, WebhookSignatureError
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status as http_status

GENIUS_STATUS_MAP = {
    "completed": PaymentStatus.SUCCESS,
    "success": PaymentStatus.SUCCESS,
    "failed": PaymentStatus.FAILED,
    "cancelled": PaymentStatus.CANCELLED,
    "refunded": PaymentStatus.REFUNDED,
    "expired": PaymentStatus.EXPIRED,
    "pending": PaymentStatus.PENDING,
}

logger = logging.getLogger(__name__)

class InitiatePaymentView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=InitiatePaymentSerializer,
        responses={201: PaymentResponseSerializer},
    )
    def post(self, request):
        serializer = InitiatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        # 1. Récupération de la commande
        order_query = Order.objects.filter(id=validated["order_id"])

        if request.user.is_authenticated:
            order = order_query.filter(user=request.user).first()
        else:
            order = order_query.first()

        if not order:
            return Response(
                {"detail": "Commande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if order.status == OrderStatus.PAID:
            return Response(
                {"detail": "Cette commande est déjà payée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        amount = int(order.total)
        if amount < 200:
            return Response(
                {"detail": "Le montant minimum de paiement est de 200 XOF."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Construction du customer directement depuis l'Order ou User
        if order.user:
            customer_name = f"{order.user.first_name} {order.user.last_name}".strip() or order.user.username
            customer_phone = getattr(order.user, "phone", "") or ""
            customer_email = order.user.email or ""
        else:
            customer_name = "Client Invité"
            customer_phone = order.guest_phone or ""
            customer_email = order.guest_email or ""

        customer = {
            "name": customer_name,
            "phone": customer_phone,
            "email": customer_email,
            "country": "CI",
        }

        client = GeniusPayClient()

        try:
            data = client.create_payment(
                amount=amount,
                customer=customer,
                description=f"Commande {order.reference}",
                payment_method=validated.get("payment_method"),
                gateway=validated.get("gateway"),
                mmo_provider=validated.get("mmo_provider"),
                success_url=f"{settings.FRONTEND_URL}/checkout/success",
                error_url=f"{settings.FRONTEND_URL}/checkout/error",
                metadata={"order_id": order.id, "order_reference": order.reference},
            )
        except GeniusPayError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment = Payment.objects.create(
            order=order,
            reference=data["reference"],
            external_id=str(data.get("id", "")),
            amount=data["amount"],
            fees=data.get("fees"),
            net_amount=data.get("net_amount"),
            currency=data.get("currency", "XOF"),
            gateway=data.get("gateway", ""),
            status=GENIUS_STATUS_MAP.get((data.get("status") or "").lower(), PaymentStatus.PENDING),
            payment_url=data.get("payment_url", ""),
            environment=data.get("environment", ""),
            raw_response=data,
        )

        response_serializer = PaymentResponseSerializer(payment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class GeniusPayWebhookView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        raw_body = request.body

        signature = request.headers.get("X-Webhook-Signature", "")
        timestamp = request.headers.get("X-Webhook-Timestamp", "")
        event_type = request.headers.get("X-Webhook-Event", "")

        try:
            verify_webhook_signature(
                raw_body=raw_body,
                timestamp=timestamp,
                signature=signature,
                secret=settings.GENIUS_WEBHOOK_SECRET,
            )
        except WebhookSignatureError as e:
            logger.warning(f"Webhook GeniusPay rejeté: {e}")
            return Response({"detail": str(e)}, status=http_status.HTTP_401_UNAUTHORIZED)

        payload = request.data
        event = payload.get("event", event_type)
        data = payload.get("data", {})

        reference = data.get("reference")
        if not reference:
            return Response({"detail": "Référence manquante dans le payload."}, status=http_status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.filter(reference=reference).first()
        if not payment:
            logger.warning(f"Webhook reçu pour une référence inconnue: {reference}")
            return Response({"detail": "Paiement introuvable."}, status=http_status.HTTP_404_NOT_FOUND)

        genius_status = data.get("status", "")
        new_status = GENIUS_STATUS_MAP.get(genius_status, payment.status)

        payment.status = new_status
        payment.fees = data.get("fees", payment.fees)
        payment.net_amount = data.get("net_amount", payment.net_amount)
        payment.raw_response = payload
        payment.save(update_fields=["status", "fees", "net_amount", "raw_response", "updated_at"])

        # Mise à jour de la commande si paiement réussi
        if event == "payment.success" and payment.status == PaymentStatus.SUCCESS:
            order = payment.order
            if order.status != OrderStatus.PAID:
                order.status = OrderStatus.PAID
                order.save(update_fields=["status"])

        return Response({"success": True}, status=http_status.HTTP_200_OK)
