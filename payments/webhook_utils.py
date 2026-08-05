import hashlib
import hmac
import time


class WebhookSignatureError(Exception):
    pass


def verify_webhook_signature(raw_body: bytes, timestamp: str, signature: str, secret: str, tolerance_seconds: int = 300):
    """
    Vérifie la signature HMAC-SHA256 d'un webhook GeniusPay.
    signature attendue = HMAC-SHA256(timestamp + "." + json_payload, secret)
    """
    if not timestamp or not signature:
        raise WebhookSignatureError("Timestamp ou signature manquant.")

    # Protection contre les attaques par rejeu (replay attack)
    try:
        ts = int(timestamp)
    except ValueError:
        raise WebhookSignatureError("Timestamp invalide.")

    now = int(time.time())
    if abs(now - ts) > tolerance_seconds:
        raise WebhookSignatureError("Timestamp hors tolérance (webhook trop ancien ou horloge désynchronisée).")

    payload_to_sign = f"{timestamp}.{raw_body.decode('utf-8')}"
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        raise WebhookSignatureError("Signature invalide.")