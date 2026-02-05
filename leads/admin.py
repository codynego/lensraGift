from django.contrib import admin
from .models import Lead, InviteLink, GiftPreview, WhatsAppLog

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('whatsapp', 'name', 'invited_by', 'has_viewed_preview', 'has_shared', 'created_at')
    list_filter = ('has_viewed_preview', 'has_shared', 'created_at')
    search_fields = ('whatsapp', 'name', 'email')
    readonly_fields = ('id', 'created_at')
    
    # This helps you see how many people this person referred directly in the list
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('referrals')

@admin.register(InviteLink)
class InviteLinkAdmin(admin.ModelAdmin):
    list_display = ('code', 'owner', 'clicks', 'created_at')
    search_fields = ('code', 'owner__whatsapp')
    readonly_fields = ('created_at',)

@admin.register(GiftPreview)
class GiftPreviewAdmin(admin.ModelAdmin):
    list_display = ('lead', 'preview_type', 'created_at')
    list_filter = ('preview_type', 'created_at')
    search_fields = ('lead__whatsapp', 'lead__name')

@admin.register(WhatsAppLog)
class WhatsAppLogAdmin(admin.ModelAdmin):
    list_display = ('lead', 'message_type', 'sent_at')
    list_filter = ('message_type', 'sent_at')
    search_fields = ('lead__whatsapp',)