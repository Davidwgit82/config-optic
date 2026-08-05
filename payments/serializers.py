from rest_framework import serializers


class InitiatePaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(
        choices=["wave", "orange_money", "mtn_money"],
        required=False,
    )
    gateway = serializers.ChoiceField(
        choices=["wave", "pawapay", "orange_money", "mtn_momo", "moov_money"],
        required=False,
    )
    mmo_provider = serializers.CharField(required=False, allow_blank=True)


class PaymentResponseSerializer(serializers.Serializer):
    reference = serializers.CharField()
    payment_url = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=0)