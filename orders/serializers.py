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
            'quantity', 'total_price'
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
        
        items_to_process = []
        
        if user:
            cart_items = CartItem.objects.filter(user=user)
            if not cart_items.exists():
                raise serializers.ValidationError({"error": "Your bag is empty."})
            
            for item in cart_items:
                if item.placement:
                    price = item.placement.product.base_price
                elif item.product:
                    price = item.product.base_price
                else:
                    continue

                items_to_process.append({
                    'placement': item.placement,
                    'product': item.product,
                    'quantity': item.quantity,
                    'price': price
                })
        else:
            if not items_data:
                raise serializers.ValidationError({"error": "No items provided."})
            
            for item in items_data:
                # Support multiple naming conventions from local storage
                p_id = item.get('product_id') or item.get('product')
                pl_id = item.get('placement') or item.get('placement_details', {}).get('id')

                if pl_id:
                    try:
                        placement = DesignPlacement.objects.get(id=pl_id)
                        items_to_process.append({
                            'placement': placement,
                            'product': None,
                            'quantity': item.get('quantity', 1),
                            'price': placement.product.base_price
                        })
                    except DesignPlacement.DoesNotExist: continue
                elif p_id:
                    try:
                        product = Product.objects.get(id=p_id)
                        items_to_process.append({
                            'placement': None,
                            'product': product,
                            'quantity': item.get('quantity', 1),
                            'price': product.base_price
                        })
                    except Product.DoesNotExist: continue

        order = Order.objects.create(
            user=user,
            order_number=str(uuid.uuid4()).split('-')[0].upper(),
            total_amount=0,
            **validated_data
        )

        total = 0
        for item in items_to_process:
            unit_price = item['price']
            qty = item['quantity']
            subtotal = unit_price * qty
            
            OrderItem.objects.create(
                order=order,
                placement=item['placement'],
                product=item['product'],
                quantity=qty,
                unit_price=unit_price,
                subtotal=subtotal
            )
            total += subtotal

        order.total_amount = total
        order.save()

        if user:
            CartItem.objects.filter(user=user).delete()
            
        return order