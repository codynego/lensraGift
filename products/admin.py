from django.contrib import admin
from .models import Product, PrintableArea


class PrintableAreaInline(admin.TabularInline):
    """Inline admin for PrintableArea."""
    model = PrintableArea
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""

    list_display = ['name', 'category', 'base_price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    inlines = [PrintableAreaInline]


@admin.register(PrintableArea)
class PrintableAreaAdmin(admin.ModelAdmin):
    """Admin configuration for PrintableArea model."""

    list_display = ['product', 'name', 'x_position', 'y_position', 'width', 'height']
    list_filter = ['product']
    search_fields = ['name', 'product__name']
