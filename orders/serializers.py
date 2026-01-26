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
import uuid
from rest_framework import serializers
from django.conf import settings
from django.db import transaction
from .models import Order, OrderItem, ShippingLocation, ShippingOption
from .models import CartItem #

class OrderCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    session_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address_id = serializers.IntegerField(write_only=True, required=False)
    
    # New required fields for the shipping system
    shipping_location_id = serializers.IntegerField(write_only=True)
    shipping_option_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'guest_email', 
            'session_id', 'address_id', 'shipping_location_id', 'shipping_option_id'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        address_id = attrs.get('address_id')
        
        # 1. Handle Saved Address vs Manual Entry
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
                raise serializers.ValidationError({f: "This field is required." for f in missing})
            
            if not user and not attrs.get('guest_email'):
                raise serializers.ValidationError({"guest_email": "Email is required for guest checkout."})

        # 2. Validate Shipping Selections
        try:
            attrs['location_obj'] = ShippingLocation.objects.get(id=attrs.get('shipping_location_id'))
            attrs['option_obj'] = ShippingOption.objects.get(id=attrs.get('shipping_option_id'))
        except ShippingLocation.DoesNotExist:
            raise serializers.ValidationError({"shipping_location_id": "Invalid shipping location."})
        except ShippingOption.DoesNotExist:
            raise serializers.ValidationError({"shipping_option_id": "Invalid shipping option."})
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        
        # Extract custom data
        session_id = validated_data.pop('session_id', None)
        address_id = validated_data.pop('address_id', None)
        location = validated_data.pop('location_obj')
        option = validated_data.pop('option_obj')
        
        # Pop IDs to avoid passing them to the Order.objects.create (since we use the objects)
        validated_data.pop('shipping_location_id')
        validated_data.pop('shipping_option_id')

        # 3. Identify Cart
        if user:
            cart_queryset = CartItem.objects.filter(user=user)
        else:
            cart_queryset = CartItem.objects.filter(session_id=session_id)

        if not cart_queryset.exists():
            raise serializers.ValidationError({"error": "Your bag is empty."})

        # 4. Determine Shipping Costs (Snapshots)
        base_fee = location.zone.base_fee
        option_fee = option.additional_cost
        total_shipping = base_fee + option_fee

        # 5. Create Order Instance
        order = Order.objects.create(
            user=user,
            session_id=session_id, 
            order_number=f"LRG-{uuid.uuid4().hex[:8].upper()}",
            shipping_location=location,
            shipping_option=option,
            shipping_base_cost=base_fee,
            shipping_option_cost=option_fee,
            total_amount=0, # Placeholder
            **validated_data
        )

        # 6. Process Items and Transfer Reveal Data
        product_subtotal = 0
        for item in cart_queryset:
            price = item.product.base_price
            if item.variant and item.variant.price_override:
                price = item.variant.price_override

            subtotal = price * item.quantity
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                placement=item.placement,
                quantity=item.quantity,
                unit_price=price,
                subtotal=subtotal,
                secret_message=item.secret_message,
                emotion=item.emotion
            )
            product_subtotal += subtotal

        # 7. Update Final Financials
        order.subtotal_amount = product_subtotal
        order.total_amount = product_subtotal + total_shipping
        order.save()

        # 8. Clear Cart
        cart_queryset.delete()
            
        return order

# For the detail view
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_email = serializers.SerializerMethodField()
    total_shipping = serializers.ReadOnlyField(source='total_shipping_cost')
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'subtotal_amount', 'total_amount', 
            'total_shipping', 'shipping_address', 'shipping_city', 
            'shipping_state', 'shipping_country', 'phone_number', 'is_paid', 
            'customer_email', 'guest_email', 'created_at', 'items',
        ]
        read_only_fields = ['id', 'order_number', 'total_amount', 'is_paid', 'created_at']

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else obj.guest_email


# serializers.py
from rest_framework import serializers
from .models import ShippingZone, ShippingLocation, ShippingOption

class ShippingLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingLocation
        fields = ['id', 'city_name']

class ShippingZoneSerializer(serializers.ModelSerializer):
    # This nests the cities inside each zone
    locations = ShippingLocationSerializer(many=True, read_only=True)

    class Meta:
        model = ShippingZone
        fields = ['id', 'name', 'base_fee', 'locations']

class ShippingOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingOption
        fields = ['id', 'name', 'additional_cost', 'estimated_delivery']