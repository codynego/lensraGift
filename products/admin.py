from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Product, ProductImage, PrintableArea, 
    DesignPlacement, Attribute, AttributeValue, ProductVariant, Tag
)


# admin.py
from django import forms
from django.utils.text import slugify
from .models import Product, Tag


class ProductAdminForm(forms.ModelForm):
    tag_input = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas (e.g. birthday, romantic, for her)"
    )

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Populate tag_input when editing
        if self.instance.pk:
            self.fields["tag_input"].initial = ", ".join(
                self.instance.tags.values_list("name", flat=True)
            )

    def save(self, commit=True):
        product = super().save(commit=False)

        if commit:
            product.save()

        # Clear existing tags
        product.tags.clear()

        tag_string = self.cleaned_data.get("tag_input", "")
        tag_names = [
            t.strip().lower()
            for t in tag_string.split(",")
            if t.strip()
        ]

        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={"slug": slugify(name)}
            )
            product.tags.add(tag)

        return product



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
    list_display = ('get_full_path', 'slug')  # Updated to show hierarchy
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)  # Added filter by parent
    search_fields = ('name', 'parent__name')  # Search by name or parent name
    
    # Add 'parent' to the form fields
    fields = ('name', 'slug', 'parent')

    def get_full_path(self, obj):
        # Build a breadcrumb-style path: "Grandparent > Parent > Name"
        path = []
        current = obj
        while current:
            path.append(current.name)
            current = current.parent
        return ' > '.join(reversed(path)) if path else obj.name
    get_full_path.short_description = 'Category Path'

@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [AttributeValueInline]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm

    list_display = (
        'name', 'get_categories', 'get_tags', 'base_price',
        'min_order_quantity', 'is_active', 'is_featured', 'is_trending'
    )

    list_filter = ('categories', 'tags', 'is_active', 'is_featured', 'is_trending')
    search_fields = ('name', 'categories__name', 'tags__name')

    prepopulated_fields = {'slug': ('name',)}

    inlines = [ProductImageInline, ProductVariantInline, PrintableAreaInline]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'slug',
                'categories',
                'tag_input',   # 👈 replaces direct tag selection
                'image',
                'base_price',
                'description'
            )
        }),
        ('Inventory Settings', {
            'fields': ('min_order_quantity', 'is_customizable')
        }),
        ('Status & Visibility', {
            'fields': (('is_active', 'is_featured', 'is_trending'),)
        }),
    )

    def get_categories(self, obj):
        return ", ".join(
            [cat.get_full_path() for cat in obj.categories.all()]
        )
    get_categories.short_description = 'Categories'

    def get_tags(self, obj):
        return ", ".join([t.name for t in obj.tags.all()])
    get_tags.short_description = 'Gift Finder Tags'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'categories', 'tags'
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