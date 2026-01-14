from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, PrintableArea, DesignPlacement

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

class PrintableAreaInline(admin.TabularInline):
    model = PrintableArea
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_customizable', 'is_active', 'image_preview')
    list_filter = ('category', 'is_customizable', 'is_active', 'is_featured', 'is_trending')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PrintableAreaInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: auto; border-radius: 4px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Preview"

@admin.register(DesignPlacement)
class DesignPlacementAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'get_user', 'created_at', 'visual_preview')
    list_filter = ('created_at', 'product')
    readonly_fields = ('created_at', 'visual_preview', 'design_details')
    
    def get_user(self, obj):
        return obj.design.user if obj.design.user else "Guest"
    get_user.short_description = "User"

    def visual_preview(self, obj):
        # Shows the mockup image the user created in the list view
        if obj.preview_mockup:
            return format_html('<img src="{}" style="width: 100px; height: auto; border: 1px solid #ddd;" />', obj.preview_mockup.url)
        # Fallback to the design's preview if mockup doesn't exist yet
        elif obj.design.preview_image:
            return format_html('<img src="{}" style="width: 100px; height: auto; border: 1px solid #ddd;" />', obj.design.preview_image.url)
        return "No Preview"
    visual_preview.short_description = "Mockup"

    def design_details(self, obj):
        # A helper to show instructions directly in the placement view
        return format_html(
            "<strong>Custom Text:</strong> {}<br><strong>Notes:</strong> {}",
            obj.design.custom_text or "None",
            obj.design.overall_instructions or "None"
        )
    design_details.short_description = "Design Info"