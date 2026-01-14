from django.contrib import admin
from .models import CartItem, Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # Make these read-only to prevent accidental changes to historical data
    readonly_fields = ('placement', 'quantity', 'unit_price', 'subtotal')
    fields = ('placement', 'quantity', 'unit_price', 'subtotal')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'is_paid', 'created_at')
    list_filter = ('status', 'is_paid', 'created_at', 'shipping_country')
    search_fields = ('order_number', 'user__email', 'phone_number', 'payment_reference')
    readonly_fields = ('order_number', 'total_amount', 'created_at', 'updated_at')
    
    # Organize the detailed view
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'user', 'status', 'total_amount', 'is_paid', 'paid_at')
        }),
        ('Shipping Details', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state', 'shipping_country', 'phone_number')
        }),
        ('Payment Details', {
            'fields': ('payment_reference',)
        }),
    )
    
    inlines = [OrderItemInline]

from django.contrib import admin
from .models import CartItem

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    # Display these columns in the list view
    list_display = ('id', 'user', 'get_item_name', 'quantity', 'get_total_price')
    list_filter = ('user',)
    search_fields = ('user__username', 'product__name', 'placement__design__name')

    def get_item_name(self, obj):
        """Displays the Custom Design name or the Plain Product name."""
        if obj.placement:
            return f"Custom: {obj.placement.product.name} ({obj.placement.design.name})"
        if obj.product:
            return f"Plain: {obj.product.name}"
        return "Unknown Item"
    get_item_name.short_description = 'Item'

    def get_total_price(self, obj):
        """Displays the calculated total price from the model property."""
        return f"₦{obj.total_price:,.2f}"
    get_total_price.short_description = 'Total Price'

    # Organize the detail view
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Item Selection', {
            'description': 'Provide EITHER a Placement (Custom) or a Product (Plain).',
            'fields': ('placement', 'product')
        }),
        ('Order Details', {
            'fields': ('quantity',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'unit_price', 'subtotal')
    
    def product_name(self, obj):
        return obj.placement.product.name