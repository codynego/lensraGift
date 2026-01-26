from django.contrib import admin
from .models import CartItem, Order, OrderItem

# 1. ORDER ITEMS INLINE
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Added 'variant' visibility to the inline
    readonly_fields = ('get_item_name', 'quantity', 'unit_price', 'subtotal', 'reveal_token', 'secret_message')
    fields = ('get_item_name', 'quantity', 'unit_price', 'subtotal', 'reveal_token', 'secret_message')

    def get_item_name(self, obj):
        """Displays name + attributes (Size/Color) safely."""
        name = "Unknown Item"
        if obj.placement and obj.placement.product:
            name = f"Custom: {obj.placement.product.name}"
        elif obj.product:
            name = f"Plain: {obj.product.name}"
        
        # Append Variant attributes if they exist
        if obj.variant:
            attrs = ", ".join([f"{a.attribute.name}: {a.value}" for a in obj.variant.attributes.all()])
            return f"{name} [{attrs}]"
        return name
    get_item_name.short_description = 'Item & Attributes'


# 2. ORDER ADMIN
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Added 'shipping_location' and 'status' colors/logic would go here
    list_display = (
        'order_number', 'get_customer', 'status', 'is_paid', 
        'subtotal_amount', 'total_amount', 'created_at'
    )
    list_filter = ('status', 'is_paid', 'created_at', 'shipping_option', 'shipping_location__zone')
    search_fields = ('order_number', 'user__email', 'guest_email', 'phone_number', 'shipping_city')
    
    # These are numbers calculated by the system, so they should be read-only
    readonly_fields = (
        'order_number', 'subtotal_amount', 'total_amount', 
        'shipping_base_cost', 'shipping_option_cost', 
        'created_at', 'updated_at', 'paid_at'
    )
    
    fieldsets = (
        ('Customer Info', {
            'fields': ('order_number', 'user', 'guest_email', 'session_id', 'phone_number')
        }),
        ('Status & Payment', {
            'fields': ('status', 'is_paid', 'paid_at', 'payment_reference')
        }),
        ('Financial Breakdown', {
            'description': 'Snapshot of prices at the time of purchase.',
            'fields': (
                'subtotal_amount', 
                'shipping_base_cost', 
                'shipping_option_cost', 
                'total_amount'
            )
        }),
        ('Shipping Logistics', {
            'fields': (
                'shipping_location', 
                'shipping_option', 
                'shipping_address', 
                'shipping_city', 
                'shipping_state', 
                'shipping_country'
            )
        }),
    )
    
    inlines = [OrderItemInline]

    def get_customer(self, obj):
        if obj.user:
            return obj.user.email
        return obj.guest_email if obj.guest_email else f"Guest ({obj.session_id[:8] if obj.session_id else 'N/A'})"
    
    get_customer.short_description = 'Customer'

# 3. CART ITEM ADMIN
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_owner', 'get_item_name', 'quantity', 'get_total_price')
    list_filter = ('user',)
    # Added variant attributes to search
    search_fields = ('user__username', 'product__name', 'variant__attributes__value', 'session_id')

    def get_owner(self, obj):
        return obj.user.email if obj.user else f"Guest ({obj.session_id[:8]}...)"

    def get_item_name(self, obj):
        """Shows product name plus the chosen variant (Size/Color)."""
        name = obj.product.name if obj.product else "Empty Slot"
        if obj.variant:
            attrs = ", ".join([f"{a.attribute.name}: {a.value}" for a in obj.variant.attributes.all()])
            name = f"{name} ({attrs})"
        
        if obj.placement:
            return f"🎨 {name} (Custom Design)"
        return f"👕 {name} (Plain)"
    get_item_name.short_description = 'Item Details'

    def get_total_price(self, obj):
        return f"₦{obj.total_price:,.2f}"


# 4. ORDER ITEM ADMIN
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_full_info', 'quantity', 'unit_price', 'subtotal', 'reveal_token', 'secret_message')
    search_fields = ('order__order_number', 'product__name', 'variant__attributes__value', 'reveal_token', 'secret_message')

    def product_full_info(self, obj):
        """Comprehensive string showing Product, Design, and Variants."""
        base_name = obj.product.name if obj.product else "No Product"
        
        # Add Variant info
        variant_info = ""
        if obj.variant:
            attrs = ", ".join([f"{a.attribute.name}: {a.value}" for a in obj.variant.attributes.all()])
            variant_info = f" [{attrs}]"
        
        # Add Design info
        design_info = ""
        if obj.placement and obj.placement.design:
            design_info = f" / Design: {obj.placement.design.name}"
            
        return f"{base_name}{variant_info}{design_info}"
    
    product_full_info.short_description = 'Product Details'





from django.contrib import admin
from .models import ShippingZone, ShippingLocation, ShippingOption

class ShippingLocationInline(admin.TabularInline):
    model = ShippingLocation
    extra = 3  # Gives you 3 empty rows to quickly type cities

@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    inlines = [ShippingLocationInline]
    list_display = ('name', 'base_fee')

@admin.register(ShippingOption)
class ShippingOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'additional_cost', 'estimated_delivery')