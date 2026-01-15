from django.contrib import admin
from .models import CartItem, Order, OrderItem

# 1. ORDER ITEMS INLINE
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Added 'variant' visibility to the inline
    readonly_fields = ('get_item_name', 'quantity', 'unit_price', 'subtotal')
    fields = ('get_item_name', 'quantity', 'unit_price', 'subtotal')

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
    list_display = ('order_number', 'get_customer', 'status', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid', 'created_at', 'shipping_country')
    search_fields = ('order_number', 'user__email', 'guest_email', 'phone_number')
    readonly_fields = ('order_number', 'total_amount', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Customer Info', {
            'fields': ('order_number', 'user', 'guest_email', 'session_id')
        }),
        ('Status & Payment', {
            'fields': ('status', 'total_amount', 'is_paid', 'paid_at', 'payment_reference')
        }),
        ('Shipping Details', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state', 'shipping_country', 'phone_number')
        }),
    )
    
    inlines = [OrderItemInline]

    def get_customer(self, obj):
        return obj.user.email if obj.user else (obj.guest_email or f"Guest {obj.session_id[:8]}")
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
    list_display = ('order', 'product_full_info', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('order__order_number', 'product__name', 'variant__attributes__value')

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