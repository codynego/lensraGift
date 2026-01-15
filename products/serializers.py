from rest_framework import serializers
from .models import (
    Product, ProductImage, PrintableArea, DesignPlacement, 
    Category, Attribute, AttributeValue, ProductVariant
)
from designs.models import Design 

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

# --- NEW IMAGE SERIALIZER ---

class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for the additional gallery images."""
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text']

# --- ATTRIBUTE SERIALIZERS ---

class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name', read_only=True)

    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute_name', 'value']

class ProductVariantSerializer(serializers.ModelSerializer):
    attributes = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'attributes', 'price_override', 'stock_quantity']

# --- PRODUCT SERIALIZERS ---

class PrintableAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrintableArea
        fields = ['id', 'name', 'x', 'y', 'width', 'height']

class ProductSerializer(serializers.ModelSerializer):
    """Detailed view for Product Page and Editor."""
    printable_areas = PrintableAreaSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    # NEW: Include the gallery images
    gallery = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 'gallery', # Added gallery
            'min_order_quantity', 'description', 'is_customizable', 
            'printable_areas', 'variants', 'category_name',
            'is_featured', 'is_trending', 'is_active'
        ]
        read_only_fields = ['id', 'is_trending', 'is_featured', 'is_active', 'is_customizable']

class ProductListSerializer(serializers.ModelSerializer):
    """Simplified view for the product grid/shop home."""
    variants = ProductVariantSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 
            'min_order_quantity', 'is_featured', 'is_customizable', 
            'is_trending', 'variants'
        ]

class DesignPlacementSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_price = serializers.ReadOnlyField(source='product.base_price')
    
    design_name = serializers.ReadOnlyField(source='design.name')
    design_preview = serializers.ImageField(source='design.preview_image', read_only=True)
    custom_text = serializers.ReadOnlyField(source='design.custom_text')
    overall_instructions = serializers.ReadOnlyField(source='design.overall_instructions')

    class Meta:
        model = DesignPlacement
        fields = [
            'id', 'design', 'product', 'printable_area', 
            'layout_data', 'preview_mockup',
            'product_name', 'product_image', 'product_price',
            'design_name', 'design_preview', 'custom_text', 'overall_instructions'
        ]

    def validate(self, data):
        product = data.get('product')
        printable_area = data.get('printable_area')

        if printable_area and product:
            if printable_area.product != product:
                raise serializers.ValidationError(
                    {"printable_area": "This area does not belong to the selected product."}
                )
        return data