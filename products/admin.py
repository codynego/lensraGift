from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductImage, PrintableArea, 
    DesignPlacement, Attribute, AttributeValue, ProductVariant
)

# --- INLINES ---

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Allows uploading 3 gallery images at once
    fields = ('image', 'alt_text')

class PrintableAreaInline(admin.TabularInline):
    model = PrintableArea
    extra = 1

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    # Important: attributes is a ManyToMany field, so we use this for a better UI
    filter_horizontal = ('attributes',)

class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 3

# --- ADMIN CLASSES ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [AttributeValueInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'base_price', 'min_order_quantity', 
        'is_active', 'is_featured', 'is_trending'
    )
    list_filter = ('category', 'is_active', 'is_featured', 'is_trending')
    search_fields = ('name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    
    # NEW: All related sections are now managed inside the Product page
    inlines = [ProductImageInline, ProductVariantInline, PrintableAreaInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'image', 'base_price', 'description')
        }),
        ('Inventory Settings', {
            'fields': ('min_order_quantity', 'is_customizable')
        }),
        ('Status & Visibility', {
            'fields': ('is_active', 'is_featured', 'is_trending')
        }),
    )

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'get_attributes', 'price_override', 'stock_quantity')
    list_filter = ('product', 'attributes__attribute')

    def get_attributes(self, obj):
        return ", ".join([f"{a.attribute.name}: {a.value}" for a in obj.attributes.all()])
    get_attributes.short_description = 'Applied Attributes'

@admin.register(DesignPlacement)
class DesignPlacementAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'get_user', 'created_at', 'visual_preview')
    list_filter = ('created_at', 'product')
    readonly_fields = ('created_at', 'visual_preview', 'design_details')
    
    def get_user(self, obj):
        return obj.design.user.email if (obj.design.user and obj.design.user.email) else "Guest"

    def visual_preview(self, obj):
        if obj.preview_mockup:
            return format_html('<img src="{}" style="width: 100px; height: auto; border-radius: 8px;" />', obj.preview_mockup.url)
        return "No Preview"
    visual_preview.short_description = "Mockup"

    def design_details(self, obj):
        return format_html(
            "<strong>Custom Text:</strong> {}<br><strong>Notes:</strong> {}",
            obj.design.custom_text or "None",
            obj.design.overall_instructions or "None"
        )