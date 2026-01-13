from django.contrib import admin
from django.utils.html import format_html
from .models import Design

@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    """Admin configuration for Design model."""

    # list_display with a thumbnail for quick visual identification
    list_display = ['get_preview', 'name', 'user', 'is_featured', 'created_at']
    list_filter = ['created_at', 'is_featured']
    search_fields = ['name', 'user__email']
    
    # Protecting the core design data and timestamps
    readonly_fields = ['design_data', 'created_at', 'updated_at', 'preview_display']

    def get_preview(self, obj):
        """Small thumbnail for the list view."""
        if obj.preview_image:
            return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 4px; border: 1px solid #eee;" />', obj.preview_image.url)
        return "No Preview"
    get_preview.short_description = 'Preview'

    def preview_display(self, obj):
        """Large preview for the detail view."""
        if obj.preview_image:
            return format_html('<img src="{}" style="max-width: 500px; height: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);" />', obj.preview_image.url)
        return "No Image Uploaded"
    preview_display.short_description = "Full Design Preview"