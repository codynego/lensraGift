from rest_framework import serializers
from .models import Product, PrintableArea


class PrintableAreaSerializer(serializers.ModelSerializer):
    """Serializer for PrintableArea model."""

    class Meta:
        model = PrintableArea
        fields = ['id', 'name', 'x_position', 'y_position', 'width', 'height']


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model."""

    printable_areas = PrintableAreaSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description','slug', 'base_price', 'category', 'is_featured', 'is_trending', 'views_count',
            'image', 'is_active', 'printable_areas', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'views_count', 'is_featured', 'is_trending']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listings."""

    class Meta:
        model = Product
        fields = ['id', 'name', 'base_price', 'category', 'image', 'is_active', 'is_featured', 'is_trending']
