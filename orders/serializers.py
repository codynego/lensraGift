from rest_framework import serializers
from .models import CartItem, Order, OrderItem
from products.serializers import DesignPlacementSerializer, ProductSerializer # Import your existing serializer
from rest_framework import serializers
from .models import CartItem, Product, DesignPlacement

class CartItemSerializer(serializers.ModelSerializer):
    # These read-only fields will pull the full objects
    product_details = ProductSerializer(source='product', read_only=True)
    placement_details = DesignPlacementSerializer(source='placement', read_only=True)
    
    # Keep these for writing (adding to cart)
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), required=False, allow_null=True
    )
    placement = serializers.PrimaryKeyRelatedField(
        queryset=DesignPlacement.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_details', 
            'placement', 'placement_details', 
            'quantity', 'total_price', 'session_id'
        ]


import uuid
from rest_framework import serializers
from .models import Order, OrderItem, CartItem
from products.models import DesignPlacement, Product

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.SerializerMethodField()
    design_preview = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'design_preview', 'quantity', 'unit_price', 'subtotal']

    def get_product_name(self, obj):
        # Check placement first, then fallback to plain product
        if obj.placement and obj.placement.product:
            return obj.placement.product.name
        if obj.product:
            return obj.product.name
        return "Unknown Product"

    def get_design_preview(self, obj):
        # Only return a design preview if it's a custom placement
        if obj.placement and obj.placement.design:
            request = self.context.get('request')
            if obj.placement.design.preview_image:
                photo_url = obj.placement.design.preview_image.url
                return request.build_absolute_uri(photo_url) if request else photo_url
        return None

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
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
    items_data = serializers.JSONField(write_only=True, required=False)
    session_id = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = [
            'shipping_address', 'shipping_city', 'shipping_state', 
            'shipping_country', 'phone_number', 'guest_email', 
            'items_data', 'session_id'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request.user and request.user.is_authenticated else None
        items_data = validated_data.pop('items_data', None)
        session_id = validated_data.pop('session_id', None)
        
        items_to_process = []
        cart_queryset = None

        # 1. IDENTIFY THE SOURCE OF ITEMS
        if user:
            cart_queryset = CartItem.objects.filter(user=user)
        elif session_id:
            cart_queryset = CartItem.objects.filter(session_id=session_id)

        # 2. PROCESS DATABASE ITEMS (User or Session)
        if cart_queryset and cart_queryset.exists():
            for item in cart_queryset:
                price = item.placement.product.base_price if item.placement else item.product.base_price
                items_to_process.append({
                    'placement': item.placement,
                    'product': item.product,
                    'quantity': item.quantity,
                    'price': price
                })
        # 3. FALLBACK TO MANUAL DATA (Legacy/LocalStorage)
        elif items_data:
            for item in items_data:
                p_id = item.get('product_id') or item.get('product')
                pl_id = item.get('placement') or item.get('placement_details', {}).get('id')

                if pl_id:
                    placement = DesignPlacement.objects.filter(id=pl_id).first()
                    if placement:
                        items_to_process.append({
                            'placement': placement, 'product': None,
                            'quantity': item.get('quantity', 1),
                            'price': placement.product.base_price
                        })
                elif p_id:
                    product = Product.objects.filter(id=p_id).first()
                    if product:
                        items_to_process.append({
                            'placement': None, 'product': product,
                            'quantity': item.get('quantity', 1),
                            'price': product.base_price
                        })

        if not items_to_process:
            raise serializers.ValidationError({"error": "Your bag is empty or items could not be found."})

        # 4. CREATE THE ORDER
        order = Order.objects.create(
            user=user,
            session_id=session_id, # Link the guest session to the order
            order_number=f"LRG-{uuid.uuid4().hex[:8].upper()}",
            total_amount=0,
            **validated_data
        )

        total = 0
        for item in items_to_process:
            subtotal = item['price'] * item['quantity']
            OrderItem.objects.create(
                order=order,
                placement=item['placement'],
                product=item['product'],
                quantity=item['quantity'],
                unit_price=item['price'],
                subtotal=subtotal
            )
            total += subtotal

        order.total_amount = total
        order.save()

        # 5. CLEANUP CART
        if cart_queryset:
            cart_queryset.delete()
            
        return order