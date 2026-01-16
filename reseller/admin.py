from django.contrib import admin, messages
from django.utils import timezone
from .models import ResellerProfile, WalletTransaction

@admin.action(description="Approve selected resellers")
def approve_resellers(modeladmin, request, queryset):
    updated = queryset.update(status='APPROVED', approved_at=timezone.now())
    messages.success(request, f"{updated} resellers have been approved.")

class WalletTransactionInline(admin.TabularInline):
    model = WalletTransaction
    extra = 0
    readonly_fields = ('timestamp', 'transaction_type', 'amount', 'order', 'description')
    can_delete = False

@admin.register(ResellerProfile)
class ResellerProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'business_name', 'status', 'wallet_balance', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('user__email', 'business_name', 'whatsapp_number')
    actions = [approve_resellers]
    inlines = [WalletTransactionInline]
    
    # Organize fields into sections
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'status', 'approved_at')
        }),
        ('Business Details', {
            'fields': ('business_name', 'whatsapp_number', 'marketing_plan')
        }),
        ('Financials', {
            'fields': ('wallet_balance',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('reseller', 'transaction_type', 'amount', 'timestamp', 'order')
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('reseller__user__email', 'description')
    readonly_fields = ('timestamp',)