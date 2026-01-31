from django.contrib import admin
from .models import CartItem, Order, OrderItem, Coupon, CouponRedemption, ShippingZone, ShippingLocation, ShippingOption

# 1. ORDER ITEMS INLINE
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Added Surprise Reveal fields for visibility
    readonly_fields = ('get_item_name', 'quantity', 'unit_price', 'subtotal', 'reveal_token', 'secret_message', 'emotion')
    fields = ('get_item_name', 'quantity', 'unit_price', 'subtotal', 'reveal_token', 'secret_message', 'emotion')

    def get_item_name(self, obj):
        name = obj.product.name if obj.product else "Unknown Item"
        if obj.variant:
            attrs = ", ".join([f"{a.attribute.name}: {a.value}" for a in obj.variant.attributes.all()])
            return f"{name} [{attrs}]"
        return name
    get_item_name.short_description = 'Item & Attributes'


# 2. COUPON REDEMPTION INLINE (For Order View)
class CouponRedemptionInline(admin.StackedInline):
    model = CouponRedemption
    extra = 0
    readonly_fields = ('coupon', 'redeemed_at')
    can_delete = False


# 3. COUPON ADMIN
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'is_active', 'used_count', 'max_uses', 'expires_at')
    list_filter = ('discount_type', 'is_active', 'created_at')
    search_fields = ('code',)
    readonly_fields = ('used_count', 'created_at')
    
    fieldsets = (
        ('General Info', {
            'fields': ('code', 'is_active', 'created_at')
        }),
        ('Discount Logic', {
            'fields': ('discount_type', 'value', 'min_order_amount')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'used_count', 'expires_at')
        }),
    )


# 4. ORDER ADMIN
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'get_customer', 'status', 'is_paid', 
        'payable_amount', 'discount_amount', 'created_at'
    )
    list_filter = ('status', 'is_paid', 'created_at', 'applied_coupon')
    search_fields = ('order_number', 'user__email', 'guest_email', 'phone_number')
    
    # Financial snapshots + Coupon fields are Read Only
    readonly_fields = (
        'order_number', 'subtotal_amount', 'discount_amount', 
        'total_amount', 'payable_amount', 'applied_coupon',
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
            'description': 'Snapshot of prices including applied discounts.',
            'fields': (
                'subtotal_amount', 
                'shipping_base_cost', 
                'shipping_option_cost', 
                'total_amount',
                'applied_coupon',
                'discount_amount',
                'payable_amount'
            )
        }),
        ('Shipping Logistics', {
            'fields': (
                'shipping_location', 
                'shipping_option', 
                'shipping_address', 
                'shipping_city', 
                'shipping_state'
            )
        }),
    )
    
    inlines = [OrderItemInline, CouponRedemptionInline]

    def get_customer(self, obj):
        if obj.user:
            return obj.user.email
        return obj.guest_email if obj.guest_email else f"Guest ({obj.session_id[:8]})"
    get_customer.short_description = 'Customer'


# 5. REMAINING ADMINS (Cart, Zone, Option)
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    # 'get_owner' must be defined here to be used in list_display
    list_display = ('id', 'get_owner', 'product', 'quantity', 'get_total_price')
    list_filter = ('user',)
    search_fields = ('user__email', 'product__name', 'session_id')

    def get_owner(self, obj):
        if obj.user:
            return obj.user.email
        return f"Guest ({obj.session_id[:8]}...)" if obj.session_id else "Anonymous"
    get_owner.short_description = 'Owner'

    def get_total_price(self, obj):
        # Accesses the @property total_price from your model
        return f"₦{obj.total_price:,.2f}"
    get_total_price.short_description = 'Total Price'

@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ('coupon', 'user', 'order', 'redeemed_at')
    list_filter = ('redeemed_at',)

@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_fee')

@admin.register(ShippingOption)
class ShippingOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'additional_cost', 'estimated_delivery')