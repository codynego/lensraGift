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

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_name', 'design_name', 'quantity', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__email',)

    # Helper methods to show linked data in the list view
    def product_name(self, obj):
        return obj.placement.product.name
    
    def design_name(self, obj):
        return obj.placement.design.name

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'quantity', 'unit_price', 'subtotal')
    
    def product_name(self, obj):
        return obj.placement.product.name