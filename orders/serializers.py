from rest_framework import serializers
from .models import CartItem, Order, OrderItem
from products.serializers import DesignPlacementSerializer # Import your existing serializer

class CartItemSerializer(serializers.ModelSerializer):
    # Use the updated placement serializer above
    placement_details = DesignPlacementSerializer(source='placement', read_only=True)
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = CartItem
        fields = ['id', 'placement', 'placement_details', 'quantity', 'total_price', 'added_at']
        read_only_fields = ['id', 'added_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='placement.product.name', read_only=True)
    design_preview = serializers.ImageField(source='placement.design.preview_image', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'design_preview', 'quantity', 'unit_price', 'subtotal']


import uuid
from rest_framework import serializers
from .models import Order, OrderItem, CartItem
from products.models import DesignPlacement

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    # Include guest_email so the frontend can display who bought it if no user exists
    customer_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'total_amount', 
            'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'is_paid', 
            'customer_email', 'guest_email', 'created_at', 'items'
        ]
        read_only_fields = ['id', 'order_number', 'total_amount', 'is_paid', 'created_at']

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else obj.guest_email

class OrderCreateSerializer(serializers.ModelSerializer):
    """Handles checkout for both logged-in users and guests."""
    # This field allows the frontend to send the local_cart array if the user is a guest
    items_data = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'guest_email', 'items_data'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        items_data = validated_data.pop('items_data', None)
        
        # 1. Determine the source of the items
        items_to_process = []
        
        if user:
            # Source: Database Cart
            cart_items = CartItem.objects.filter(user=user)
            if not cart_items.exists():
                raise serializers.ValidationError({"error": "Your database cart is empty."})
            for item in cart_items:
                items_to_process.append({
                    'placement': item.placement,
                    'quantity': item.quantity,
                    'price': item.placement.product.base_price
                })
        else:
            # Source: Local Storage (items_data sent from frontend)
            if not items_data:
                raise serializers.ValidationError({"error": "No items provided for guest checkout."})
            if not validated_data.get('guest_email'):
                raise serializers.ValidationError({"guest_email": "Email is required for guest checkout."})
            
            for item in items_data:
                try:
                    # Expecting item to have placement ID from local storage
                    placement_id = item.get('placement_details', {}).get('id') or item.get('placement')
                    placement = DesignPlacement.objects.get(id=placement_id)
                    items_to_process.append({
                        'placement': placement,
                        'quantity': item.get('quantity', 1),
                        'price': placement.product.base_price
                    })
                except DesignPlacement.DoesNotExist:
                    continue

        # 2. Create the Order
        order = Order.objects.create(
            user=user,
            order_number=str(uuid.uuid4()).split('-')[0].upper(),
            total_amount=0, # Placeholder
            **validated_data
        )

        # 3. Create OrderItems and calculate total
        total = 0
        for item in items_to_process:
            unit_price = item['price']
            subtotal = unit_price * item['quantity']
            
            OrderItem.objects.create(
                order=order,
                placement=item['placement'],
                quantity=item['quantity'],
                unit_price=unit_price,
                subtotal=subtotal
            )
            total += subtotal

        # 4. Finalize order amount
        order.total_amount = total
        order.save()

        # 5. Cleanup: If user was logged in, clear their DB cart
        if user:
            CartItem.objects.filter(user=user).delete()
            
        return order