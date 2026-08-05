import requests
from django.conf import settings


class GeniusPayError(Exception):
    """Levée quand l'appel à l'API GeniusPay échoue."""
    def __init__(self, message, status_code=None, response_data=None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class GeniusPayClient:
    def __init__(self):
        self.base_url = settings.GENIUS_PAY_BASE_URL.rstrip("/")
        self.headers = {
            "X-API-Key": settings.GENIUS_API_KEY,
            "X-API-Secret": settings.GENIUS_API_SECRET,
            "Content-Type": "application/json",
        }

    def create_payment(
        self,
        amount,
        customer,
        description="",
        currency="XOF",
        payment_method=None,
        gateway=None,
        mmo_provider=None,
        success_url=None,
        error_url=None,
        metadata=None,
    ):
        payload = {
            "amount": amount,
            "currency": currency,
            "customer": customer,
        }

        if description:
            payload["description"] = description[:500]
        if payment_method:
            payload["payment_method"] = payment_method
        if gateway:
            payload["gateway"] = gateway
        if mmo_provider:
            payload["mmo_provider"] = mmo_provider
        if success_url:
            payload["success_url"] = success_url
        if error_url:
            payload["error_url"] = error_url
        if metadata:
            payload["metadata"] = metadata

        try:
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=self.headers,
                timeout=15,
            )
        except requests.RequestException as e:
            raise GeniusPayError(f"Erreur réseau lors de l'appel à GeniusPay: {e}")

        try:
            data = response.json()
        except ValueError:
            raise GeniusPayError(
                "Réponse GeniusPay invalide (non-JSON)",
                status_code=response.status_code,
            )

        if not response.ok or not data.get("success"):
            raise GeniusPayError(
                data.get("message", "Échec de la création du paiement"),
                status_code=response.status_code,
                response_data=data,
            )

        return data["data"]