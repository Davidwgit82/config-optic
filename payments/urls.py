from django.urls import path
from .views import InitiatePaymentView, GeniusPayWebhookView

app_name = "payments"

urlpatterns = [
    path("initiate/", InitiatePaymentView.as_view(), name="initiate"),
    path("webhooks/geniuspay/", GeniusPayWebhookView.as_view(), name="geniuspay-webhook"),

]