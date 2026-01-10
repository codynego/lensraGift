from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model."""

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'user', 'reference', 'amount', 'status',
            'payment_method', 'access_code', 'authorization_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'reference', 'status', 'access_code',
            'authorization_url', 'created_at', 'updated_at'
        ]


class PaymentInitializeSerializer(serializers.Serializer):
    """Serializer for initializing payment."""

    order_id = serializers.IntegerField()
    email = serializers.EmailField()


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for verifying payment."""

    reference = serializers.CharField()
