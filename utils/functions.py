import random
from django.db.models import Max


def generate_sku():
    return str(random.randint(10000000, 99999999))


def generate_order_reference():
    """
    Génère une référence de commande au format :
    CMD-000001
    CMD-000002
    ...
    """

    from orders.models import Order

    last_order = (
        Order.objects.filter(reference__startswith="CMD-")
        .aggregate(max_ref=Max("reference"))
    )["max_ref"]

    if not last_order:
        return "CMD-000001"

    last_number = int(last_order.split("-")[1])
    return f"CMD-{last_number + 1:06d}"