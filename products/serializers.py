from rest_framework import serializers
from .models import Product, PrintableArea, DesignPlacement, Category
from designs.models import Design 

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class PrintableAreaSerializer(serializers.ModelSerializer):
    """Provides coordinates or labels for placement zones."""
    class Meta:
        model = PrintableArea
        fields = ['id', 'name', 'x', 'y', 'width', 'height']

class ProductSerializer(serializers.ModelSerializer):
    """Detailed view for the Editor: includes all print zones."""
    printable_areas = PrintableAreaSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 
            'is_customizable', 'printable_areas', 'category_name',
            'is_featured', 'is_trending', 'is_active'
        ]
        # Fixed typo from 'is_Featured' to 'is_featured'
        read_only_fields = ['id', 'is_trending', 'is_featured', 'is_active', 'is_customizable']

class ProductListSerializer(serializers.ModelSerializer):
    """Simplified view for the product grid."""
    printable_areas = PrintableAreaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 
            'is_featured', 'is_customizable', 'printable_areas', 'is_trending'
        ]

class DesignPlacementSerializer(serializers.ModelSerializer):
    """
    Connects a specific Product to a specific Design.
    This is what actually goes into the Cart.
    """
    product_name = serializers.ReadOnlyField(source='product.name')
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_price = serializers.ReadOnlyField(source='product.base_price')
    
    # Updated to match the new Design model fields
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
        """
        Validates that the selected printable area (if any) belongs to the product.
        """
        product = data.get('product')
        printable_area = data.get('printable_area')

        if printable_area and product:
            if printable_area.product != product:
                raise serializers.ValidationError(
                    {"printable_area": "This area does not belong to the selected product."}
                )
        return data