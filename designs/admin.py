from django.contrib import admin
from .models import Design


@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    """Admin configuration for Design model."""

    list_display = ['name', 'user', 'product', 'is_featured', 'created_at']
    list_filter = ['product', 'created_at', 'is_featured']
    search_fields = ['name', 'user__email', 'product__name']
    readonly_fields = ['preview_image', 'created_at', 'updated_at']
