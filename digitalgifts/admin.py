from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Occasion, ExperienceTier, AddOn, 
    DigitalGift, DigitalGiftAddOn
)

# --- INLINES ---

class DigitalGiftAddOnInline(admin.TabularInline):
    model = DigitalGiftAddOn
    extra = 0
    verbose_name = "Selected Add-On"
    verbose_name_plural = "Selected Add-Ons"

# --- ADMIN CLASSES ---

@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(ExperienceTier)
class ExperienceTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'recommended')
    list_editable = ('price', 'recommended')
    list_filter = ('recommended',)


@admin.register(AddOn)
class AddOnAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    list_editable = ('price',)


@admin.register(DigitalGift)
class DigitalGiftAdmin(admin.ModelAdmin):
    # Organizes the list view for quick "Order Processing"
    list_display = (
        'id', 'short_id', 'sender_name', 'recipient_name', 'occasion', 
        'tier', 'status_pill', 'payment_status', 'created_at', 'is_opened', 'open_count', 'opened_at'
    )
    list_filter = ('status', 'is_paid', 'occasion', 'tier', 'created_at')
    search_fields = ('sender_name', 'recipient_name', 'sender_email', 'recipient_email')
    ordering = ('-created_at',)
    
    # Use Inlines to manage AddOns directly inside the Gift page
    inlines = [DigitalGiftAddOnInline]

    # Custom "Status Pill" for better visibility
    def status_pill(self, obj):
        colors = {
            'pending': '#71717a',    # Zinc-500
            'processing': '#2563eb', # Blue-600
            'sent': '#9333ea',       # Purple-600
            'delivered': '#16a34a',  # Green-600
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; text-transform: uppercase;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.status
        )
    status_pill.short_description = 'Status'

        # Custom Payment Status
    def payment_status(self, obj):
        color = "#16a34a" if obj.is_paid else "#dc2626"
        label = "✔ PAID" if obj.is_paid else "✘ UNPAID"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            label
        )


    # Organize the detail view into sections
    fieldsets = (
        ('Logistics Status', {
            'fields': ('status', 'is_paid', 'delivered')
        }),
        ('Sender & Recipient', {
            'fields': (('sender_name', 'sender_email'), ('recipient_name', 'recipient_email', 'recipient_phone'))
        }),
        ('Gift Configuration', {
            'fields': ('occasion', 'tier', 'delivery_method', 'scheduled_delivery')
        }),
        ('Content', {
            'classes': ('collapse',), # Hide by default to save space
            'fields': ('text_message', 'voice_message', 'video_message'),
        }),
    )

# Optional: Customizing the Admin Site Header
admin.site.site_header = "Lensra Gifts Lab Operations"
admin.site.site_title = "Lensra Admin"
admin.site.index_title = "Gift Management System"