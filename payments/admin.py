from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin configuration for Payment model."""

    list_display = [
        'reference', 'order', 'user', 'amount',
        'status', 'payment_method', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['reference', 'order__order_number', 'user__email']
    readonly_fields = [
        'reference', 'access_code', 'authorization_url',
        'paystack_response', 'created_at', 'updated_at'
    ]
