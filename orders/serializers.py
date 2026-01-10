from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductListSerializer
from designs.serializers import DesignSerializer
import uuid


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model."""

    product_details = ProductListSerializer(source='product', read_only=True)
    design_details = DesignSerializer(source='design', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_details', 'design', 'design_details',
            'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating order items."""

    class Meta:
        model = OrderItem
        fields = ['product', 'design', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for Order model."""

    items = OrderItemSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_email', 'order_number', 'status', 'total_amount',
            'shipping_address', 'shipping_city', 'shipping_state', 'shipping_country',
            'shipping_postal_code', 'phone_number', 'payment_reference', 'is_paid',
            'paid_at', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'order_number', 'total_amount', 'payment_reference',
            'is_paid', 'paid_at', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders."""

    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_country', 'shipping_postal_code', 'phone_number', 'items'
        ]

    def validate_items(self, value):
        """Validate that order has at least one item."""
        if not value:
            raise serializers.ValidationError("Order must have at least one item.")
        return value

    def create(self, validated_data):
        """Create order with items."""
        items_data = validated_data.pop('items')
        
        # Generate unique order number
        order_number = f"ORD-{uuid.uuid4().hex[:12].upper()}"
        
        order = Order.objects.create(
            order_number=order_number,
            total_amount=0,  # Will be calculated
            **validated_data
        )
        
        total = 0
        for item_data in items_data:
            product = item_data['product']
            unit_price = product.base_price
            subtotal = unit_price * item_data['quantity']
            
            OrderItem.objects.create(
                order=order,
                unit_price=unit_price,
                subtotal=subtotal,
                **item_data
            )
            total += subtotal
        
        order.total_amount = total
        order.save()
        
        return order
