import uuid
from rest_framework import serializers
from .models import CartItem, Order, OrderItem
from products.models import Product, DesignPlacement, ProductVariant
from products.serializers import ProductSerializer, DesignPlacementSerializer, ProductVariantSerializer



from rest_framework import serializers
from django.db.models import Sum

class CartSummarySerializer(serializers.Serializer):
    total_quantity = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    wishlist_count = serializers.IntegerField() # Placeholder for future logic
    

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    placement_details = DesignPlacementSerializer(source='placement', read_only=True)
    # NEW: Full details for the selected size/color
    variant_details = ProductVariantSerializer(source='variant', read_only=True)
    
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    # NEW: Field to send when adding to cart
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
            'quantity', 'total_price', 'session_id'
        ]

# 2. ORDER ITEM SERIALIZER (Read-only for Order history)
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    design_preview = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'attributes', 'design_preview', 'quantity', 'unit_price', 'subtotal']

    def get_product_name(self, obj):
        return obj.product.name if obj.product else "Unknown Product"

    def get_attributes(self, obj):
        """Returns string like 'Color: Red, Size: XL'"""
        if obj.variant:
            return ", ".join([f"{a.attribute.name}: {a.value}" for a in obj.variant.attributes.all()])
        return None

    def get_design_preview(self, obj):
        if obj.placement and obj.placement.design:
            request = self.context.get('request')
            if obj.placement.design.preview_image:
                photo_url = obj.placement.design.preview_image.url
                return request.build_absolute_uri(photo_url) if request else photo_url
        return None

# 3. ORDER CREATE SERIALIZER (The Checkout Logic)
class OrderCreateSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    items_data = serializers.JSONField(write_only=True, required=False)
    session_id = serializers.CharField(write_only=True, required=False, allow_blank=True)
    address_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = [
            'id','shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'guest_email', 
            'items_data', 'session_id', 'address_id'
        ]

    def validate(self, attrs):
        """
        Custom validation to ensure either manual address fields OR address_id is provided.
        """
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        
        address_id = attrs.get('address_id')
        
        # If authenticated user provides address_id, populate shipping fields from saved address
        if user and address_id:
            try:
                from users.models import Address  # Adjust import based on your app structure
                address = Address.objects.get(id=address_id, user=user)
                
                # Auto-populate shipping fields from the saved address
                attrs['shipping_address'] = address.street_address
                attrs['shipping_city'] = address.city
                attrs['shipping_state'] = address.state
                attrs['shipping_country'] = 'Nigeria'
                attrs['phone_number'] = address.phone_number
                
            except Address.DoesNotExist:
                raise serializers.ValidationError({"address_id": "Invalid address selected."})
        else:
            # For guest users or manual entry, validate required fields
            required_fields = ['shipping_address', 'shipping_city', 'shipping_state', 'phone_number']
            missing = [f for f in required_fields if not attrs.get(f)]
            
            if missing:
                raise serializers.ValidationError({
                    "error": f"Missing required fields: {', '.join(missing)}"
                })
            
            # Validate guest email if user is not authenticated
            if not user and not attrs.get('guest_email'):
                raise serializers.ValidationError({"guest_email": "Email is required for guest checkout."})
        
        return attrs

    def create(self, validated_data):
        request = self.context.get('request')
        # Identify the user (None if guest)
        user = request.user if request.user and request.user.is_authenticated else None
        
        # Pop custom fields before creating the Order instance
        items_data = validated_data.pop('items_data', None)
        session_id = validated_data.pop('session_id', None)
        address_id = validated_data.pop('address_id', None)  # Remove from validated_data
        
        items_to_process = []
        cart_queryset = None

        # 1. GET ITEMS FROM DATABASE (Cart)
        # We look for cart items based on user account OR guest session
        if user:
            cart_queryset = CartItem.objects.filter(user=user)
        elif session_id:
            cart_queryset = CartItem.objects.filter(session_id=session_id)

        if not cart_queryset or not cart_queryset.exists():
            raise serializers.ValidationError({"error": "Your bag is empty."})

        # Calculate prices and prepare data
        for item in cart_queryset:
            price = item.product.base_price
            if item.variant and item.variant.price_override:
                price = item.variant.price_override

            items_to_process.append({
                'product': item.product,
                'variant': item.variant,
                'placement': item.placement,
                'quantity': item.quantity,
                'price': price
            })

        # 2. CREATE THE ORDER
        # IMPORTANT: session_id is now explicitly saved to the Order model
        order = Order.objects.create(
            user=user,
            session_id=session_id, 
            order_number=f"LRG-{uuid.uuid4().hex[:8].upper()}",
            total_amount=0,  # Will update after creating items
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
                subtotal=subtotal
            )
            total += subtotal

        # Save the calculated final total
        order.total_amount = total
        order.save()

        # 3. CLEANUP: Remove items from cart after order is placed
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