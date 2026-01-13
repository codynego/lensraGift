from django.contrib import admin
from django.utils.html import format_html
from .models import Product, PrintableArea, DesignPlacement, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class PrintableAreaInline(admin.TabularInline):
    """Allows adding Front/Back/Sleeve areas directly on the Product page."""
    model = PrintableArea
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['get_thumbnail', 'name', 'category', 'base_price', 'is_active']
    list_filter = ['category', 'is_active', 'is_customizable']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PrintableAreaInline]

    def get_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 4px; object-fit: cover;" />', obj.image.url)
        return "No Image"
    get_thumbnail.short_description = 'Img'

@admin.register(DesignPlacement)
class DesignPlacementAdmin(admin.ModelAdmin):
    """Registry of designs as applied to specific products."""
    list_display = ['id', 'get_mockup', 'product', 'printable_area', 'design']
    readonly_fields = ['layout_data', 'preview_mockup_display']
    
    def get_mockup(self, obj):
        if obj.preview_mockup:
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.preview_mockup.url)
        return "—"

    def preview_mockup_display(self, obj):
        if obj.preview_mockup:
            return format_html('<img src="{}" style="max-width: 400px;" />', obj.preview_mockup.url)
        return "No Mockup"