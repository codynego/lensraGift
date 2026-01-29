from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductImage, PrintableArea, 
    DesignPlacement, Attribute, AttributeValue, ProductVariant, Tag
)

# --- INLINES ---


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    # Displays the name and slug in the list view for easy management
    list_display = ('name', 'slug')
    
    # Automatically fills the slug field based on what you type in the name field
    prepopulated_fields = {'slug': ('name',)}
    
    # Allows you to search for tags quickly
    search_fields = ('name',)

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
    # 1. Added 'get_tags' and cleaned up the trailing empty string
    list_display = (
        'name', 'get_categories', 'get_tags', 'base_price', 
        'min_order_quantity', 'is_active', 'is_featured', 'is_trending'
    )
    
    # 2. Added 'tags' to filters so you can quickly find 'Valentine' or 'For Her' gifts
    list_filter = ('categories', 'tags', 'is_active', 'is_featured', 'is_trending')
    
    search_fields = ('name', 'categories__name', 'tags__name')
    prepopulated_fields = {'slug': ('name',)}
    
    # 3. THIS IS KEY: Makes the tag selection a nice side-by-side search box
    filter_horizontal = ('categories', 'tags')
    
    inlines = [ProductImageInline, ProductVariantInline, PrintableAreaInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', ('categories', 'tags'), 'image', 'base_price', 'description')
        }),
        ('Inventory Settings', {
            'fields': ('min_order_quantity', 'is_customizable')
        }),
        ('Status & Visibility', {
            'fields': (('is_active', 'is_featured', 'is_trending'),)
        }),
    )

    # Helper to show Categories in the list view
    def get_categories(self, obj):
        return ", ".join([c.name for c in obj.categories.all()])
    get_categories.short_description = 'Categories'

    # 4. NEW: Helper to show Tags in the list view
    def get_tags(self, obj):
        return ", ".join([t.name for t in obj.tags.all()])
    get_tags.short_description = 'Gift Finder Tags'

    def get_queryset(self, request):
        # This tells Django to "pre-fetch" the tags and categories in 
        # a single efficient query instead of one by one.
        return super().get_queryset(request).prefetch_related('categories', 'tags')

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