from django.contrib import admin
from .models import RewardProfile, RewardTransaction, RewardPerk

class RewardTransactionInline(admin.TabularInline):
    """Allows viewing transactions directly inside the Reward Profile page"""
    model = RewardTransaction
    extra = 0
    readonly_fields = ('created_at',)
    can_delete = False

@admin.register(RewardProfile)
class RewardProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'updated_at')
    search_fields = ('user__username', 'user__email')
    list_filter = ('updated_at',)
    inlines = [RewardTransactionInline]

@admin.register(RewardTransaction)
class RewardTransactionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'amount', 'transaction_type', 'description', 'coupon_code', 'is_used', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('profile__user__username', 'description')
    readonly_fields = ('created_at',)

@admin.register(RewardPerk)
class RewardPerkAdmin(admin.ModelAdmin):
    list_display = ('title', 'point_cost', 'icon_name', 'is_active')
    list_editable = ('point_cost', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')