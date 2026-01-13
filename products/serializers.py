from rest_framework import serializers
from .models import Product, PrintableArea, DesignPlacement, Category
from designs.models import Design # Assuming Design is in a separate app

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class PrintableAreaSerializer(serializers.ModelSerializer):
    """Provides coordinates to the React frontend to position the Fabric.js canvas."""
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
        read_only_fields = ['id', 'is_trending', 'is_Featured', 'is_active', 'is_customizable']

class ProductListSerializer(serializers.ModelSerializer):
    # This line is crucial! It nests the areas inside the product object
    printable_areas = PrintableAreaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'base_price', 'image', 
            'is_featured', 'is_customizable', 'printable_areas' # Add this
        ]
class DesignPlacementSerializer(serializers.ModelSerializer):
    # These fields pull data from the related models for the frontend to use
    product_name = serializers.ReadOnlyField(source='product.name')
    product_image = serializers.ImageField(source='product.image', read_only=True)
    product_price = serializers.ReadOnlyField(source='product.base_price')
    
    design_name = serializers.ReadOnlyField(source='design.name')
    design_image = serializers.ImageField(source='design.preview_image', read_only=True)

    class Meta:
        model = DesignPlacement
        fields = [
            'id', 'design', 'product', 'printable_area', 
            'layout_data', 'preview_mockup',
            'product_name', 'product_image', 'product_price',
            'design_name', 'design_image'
        ]

    def validate(self, data):
        if data['printable_area'].product != data['product']:
            raise serializers.ValidationError(
                {"printable_area": "This area does not belong to the selected product."}
            )
        return data