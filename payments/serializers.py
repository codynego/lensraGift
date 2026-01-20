import uuid
from rest_framework import serializers
from .models import Payment
from products.models import Product, DesignPlacement, ProductVariant
from products.serializers import ProductSerializer, DesignPlacementSerializer, ProductVariantSerializer

# 1. CART ITEM SERIALIZER



class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model including guest session tracking."""

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'digital_gift', 'user', 'session_id', 'reference', 'amount', 
            'status', 'payment_method', 'access_code', 'authorization_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'session_id', 'reference', 'status', 
            'access_code', 'authorization_url', 'created_at', 'updated_at'
        ]
        
        def validate(self, attrs):
            if not attrs.get('order') and not attrs.get('digital_gift'):
                raise serializers.ValidationError("Payment must be linked to either an order or a digital gift.")
            return attrs



class PaymentInitializeSerializer(serializers.Serializer):
    """Serializer for starting a payment."""

    order_id = serializers.IntegerField()
    email = serializers.EmailField()
    session_id = serializers.CharField(required=False, allow_blank=True)


class PaymentVerifySerializer(serializers.Serializer):
    """Serializer for checking if a payment was successful."""

    reference = serializers.CharField()