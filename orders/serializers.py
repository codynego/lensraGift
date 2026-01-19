import uuid
from rest_framework import serializers
from django.db.models import Sum
from .models import CartItem, Order, OrderItem
from products.models import Product, DesignPlacement, ProductVariant
from products.serializers import ProductSerializer, DesignPlacementSerializer, ProductVariantSerializer

class CartSummarySerializer(serializers.Serializer):
    total_quantity = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    wishlist_count = serializers.IntegerField() 

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    placement_details = DesignPlacementSerializer(source='placement', read_only=True)
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    variant = serializers.PrimaryKeyRelatedField(
        queryset=ProductVariant.objects.all(), required=False, allow_null=True
    )
    placement = serializers.PrimaryKeyRelatedField(
        queryset=DesignPlacement.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_details', 
            'variant', 'variant_details',
            'placement', 'placement_details', 
            'secret_message', 'emotion',  # Added Surprise Reveal fields
            'quantity', 'total_price', 'session_id'
        ]

# 2. ORDER ITEM SERIALIZER (Includes Reveal Data for the recipient)
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    design_preview = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'attributes', 'design_preview', 
            'quantity', 'unit_price', 'subtotal',
            'secret_message', 'emotion', 'reveal_token' # Added Surprise Reveal fields
        ]

    def get_product_name(self, obj):
        return obj.product.name if obj.product else "Unknown Product"

    def get_attributes(self, obj):
        """Returns string like 'Color: Red, Size: XL'"""
        if obj.variant:
            # Note: matched to attribute_name based on previous React updates
            return ", ".join([f"{a.attribute_id}: {a.value}" for a in obj.variant.attributes.all()])
        return None

    def get_design_preview(self, obj):
        if obj.placement and obj.placement.design:
            request = self.context.get('request')
            if obj.placement.design.preview_image:
                photo_url = obj.placement.design.preview_image.url
                return request.build_absolute_uri(photo_url) if request else photo_url
        return None

# 3. ORDER CREATE SERIALIZER (Transfers Cart data to Order)
class OrderCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    items_data = serializers.JSONField(write_only=True, required=False)
    session_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = [
            'id', 'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'guest_email', 
            'items_data', 'session_id', 'address_id'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        address_id = attrs.get('address_id')
        
        if user and address_id:
            try:
                from users.models import Address 
                address = Address.objects.get(id=address_id, user=user)
                attrs['shipping_address'] = address.street_address
                attrs['shipping_city'] = address.city
                attrs['shipping_state'] = address.state
                attrs['shipping_country'] = 'Nigeria'
                attrs['phone_number'] = address.phone_number
            except Address.DoesNotExist:
                raise serializers.ValidationError({"address_id": "Invalid address selected."})
        else:
            required_fields = ['shipping_address', 'shipping_city', 'shipping_state', 'phone_number']
            missing = [f for f in required_fields if not attrs.get(f)]
            if missing:
                raise serializers.ValidationError({"error": f"Missing required fields: {', '.join(missing)}"})
            
            if not user and not attrs.get('guest_email'):
                raise serializers.ValidationError({"guest_email": "Email is required for guest checkout."})
        
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        
        items_data = validated_data.pop('items_data', None)
        session_id = validated_data.pop('session_id', None)
        address_id = validated_data.pop('address_id', None)
        
        items_to_process = []
        cart_queryset = None

        if user:
            cart_queryset = CartItem.objects.filter(user=user)
        elif session_id:
            cart_queryset = CartItem.objects.filter(session_id=session_id)

        if not cart_queryset or not cart_queryset.exists():
            raise serializers.ValidationError({"error": "Your bag is empty."})

        # Process cart items and capture reveal data
        for item in cart_queryset:
            price = item.product.base_price
            if item.variant and item.variant.price_override:
                price = item.variant.price_override

            items_to_process.append({
                'product': item.product,
                'variant': item.variant,
                'placement': item.placement,
                'quantity': item.quantity,
                'price': price,
                'secret_message': item.secret_message, # Capture from cart
                'emotion': item.emotion               # Capture from cart
            })

        order = Order.objects.create(
            user=user,
            session_id=session_id, 
            order_number=f"LRG-{uuid.uuid4().hex[:8].upper()}",
            total_amount=0,
            **validated_data
        )

        total = 0
        for item in items_to_process:
            subtotal = item['price'] * item['quantity']
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                variant=item['variant'],
                placement=item['placement'],
                quantity=item['quantity'],
                unit_price=item['price'],
                subtotal=subtotal,
                secret_message=item['secret_message'], # Transfer to permanent order
                emotion=item['emotion']               # Transfer to permanent order
            )
            total += subtotal

        order.total_amount = total
        order.save()
        cart_queryset.delete()
            
        return order


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'total_amount', 
            'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'is_paid', 
            'customer_email', 'guest_email', 'created_at', 'items',
        ]
        read_only_fields = ['id', 'order_number', 'total_amount', 'is_paid', 'created_at']

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else obj.guest_email