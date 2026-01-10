from rest_framework import serializers
from .models import Design
from products.serializers import ProductListSerializer


class DesignSerializer(serializers.ModelSerializer):
    """Serializer for Design model."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_details = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = Design
        fields = [
            'id', 'user', 'user_email', 'product', 'product_details',
            'name', 'design_image', 'preview_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'preview_image', 'created_at', 'updated_at']


class DesignCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating designs."""

    class Meta:
        model = Design
        fields = ['product', 'name', 'design_image']

    def validate_design_image(self, value):
        """Validate uploaded image."""
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("Image file too large. Maximum size is 10MB.")
        
        valid_extensions = ['.jpg', '.jpeg', '.png']
        ext = value.name.lower().split('.')[-1]
        if f'.{ext}' not in valid_extensions:
            raise serializers.ValidationError("Unsupported file format. Use JPG or PNG.")
        
        return value
