import uuid
from rest_framework import serializers
from django.db.models import Sum
from .models import CartItem, Order, OrderItem
from products.models import Product, DesignPlacement, ProductVariant, Coupon, CouponRedemption
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
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Order, OrderItem, CartItem, ShippingLocation, ShippingOption, Coupon, CouponRedemption

class OrderCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    session_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address_id = serializers.IntegerField(write_only=True, required=False)
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Required IDs for logic
    shipping_location_id = serializers.IntegerField(write_only=True)
    shipping_option_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'guest_email', 
            'session_id', 'address_id', 'shipping_location_id', 
            'shipping_option_id', 'coupon_code'
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        address_id = attrs.get('address_id')
        
        # 1. Address Logic: Saved vs Manual
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
            required_manual = ['shipping_address', 'shipping_city', 'shipping_state', 'phone_number']
            for field in required_manual:
                if not attrs.get(field):
                    raise serializers.ValidationError({field: "This field is required for manual address entry."})
            
            if not user and not attrs.get('guest_email'):
                raise serializers.ValidationError({"guest_email": "Email is required for guest checkout."})

        # 2. Shipping Validation
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
        
        # Extract operational data
        session_id = validated_data.pop('session_id', None)
        coupon_code = validated_data.pop('coupon_code', None)
        location = validated_data.pop('location_obj')
        option = validated_data.pop('option_obj')
        
        # Clean up IDs before creating Order
        validated_data.pop('address_id', None)
        validated_data.pop('shipping_location_id')
        validated_data.pop('shipping_option_id')

        # 3. Cart Identification
        cart_queryset = CartItem.objects.filter(user=user) if user else CartItem.objects.filter(session_id=session_id)
        if not cart_queryset.exists():
            raise serializers.ValidationError({"error": "Your bag is empty."})

        # 4. Initialize Order (Placeholders for financials)
        order = Order.objects.create(
            user=user,
            session_id=session_id, 
            order_number=f"LRG-{uuid.uuid4().hex[:8].upper()}",
            shipping_location=location,
            shipping_option=option,
            shipping_base_cost=location.zone.base_fee,
            shipping_option_cost=option.additional_cost,
            subtotal_amount=0,
            total_amount=0,
            payable_amount=0,
            **validated_data
        )

        # 5. Process Items & Transfer Reveal Data
        product_subtotal = Decimal('0.00')
        for item in cart_queryset:
            price = item.variant.price_override if item.variant and item.variant.price_override else item.product.base_price
            
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                placement=item.placement,
                quantity=item.quantity,
                unit_price=price,
                subtotal=price * item.quantity,
                secret_message=item.secret_message,
                emotion=item.emotion
            )
            product_subtotal += (price * item.quantity)

        # 6. Coupon Logic
        discount_amount = Decimal('0.00')
        applied_coupon = None

        if coupon_code:
            try:
                coupon = Coupon.objects.get(code__iexact=coupon_code)
                if coupon.can_be_used():
                    # Check Minimum Purchase Requirement
                    if not coupon.min_order_amount or product_subtotal >= coupon.min_order_amount:
                        if coupon.discount_type == Coupon.PERCENTAGE:
                            discount_amount = (coupon.value / 100) * product_subtotal
                        else:
                            discount_amount = coupon.value
                        
                        # Apply and track
                        discount_amount = min(discount_amount, product_subtotal) # Discount can't exceed product cost
                        applied_coupon = coupon
            except Coupon.DoesNotExist:
                pass # Invalid codes are ignored or could raise an error based on preference

        # 7. Finalize Financials
        total_shipping = order.shipping_base_cost + order.shipping_option_cost
        order.subtotal_amount = product_subtotal
        order.discount_amount = discount_amount
        order.applied_coupon = applied_coupon
        order.total_amount = product_subtotal + total_shipping
        order.payable_amount = order.total_amount - discount_amount
        order.save()

        # 8. Record Redemption & Cleanup
        if applied_coupon:
            CouponRedemption.objects.create(coupon=applied_coupon, user=user, order=order)
            applied_coupon.used_count += 1
            applied_coupon.save()

        cart_queryset.delete()
        return order

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_method = serializers.ReadOnlyField(source='shipping_option.name')
    shipping_city_name = serializers.ReadOnlyField(source='shipping_location.city_name')
    coupon_code = serializers.ReadOnlyField(source='applied_coupon.code')
    total_shipping = serializers.ReadOnlyField(source='total_shipping_cost')
    customer_email = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'created_at',
            'customer_email', 'phone_number', 
            'shipping_address', 'shipping_city_name', 'shipping_state',
            'shipping_method', 'total_shipping',
            'subtotal_amount', 'discount_amount', 'coupon_code', 'payable_amount',
            'is_paid', 'paid_at', 'items'
        ]
        read_only_fields = fields

    def get_customer_email(self, obj):
        return obj.user.email if obj.user else obj.guest_email



class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'code', 'discount_type', 'value', 
            'min_order_amount', 'expires_at'
        ]


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