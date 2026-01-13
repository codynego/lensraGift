from rest_framework import serializers
from .models import Design
from products.serializers import ProductListSerializer

class DesignSerializer(serializers.ModelSerializer):
    """Full detail serializer for retrieving designs."""
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Design
        fields = [
            'id', 'user', 'user_email', 'name', 
            'design_data', 'preview_image', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class DesignCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for the initial 'Save' from the React Canvas."""
    
    class Meta:
        model = Design
        fields = ['name', 'design_data', 'preview_image', 'is_featured']

    def validate_design_data(self, value):
        """Ensure the JSON from Fabric.js isn't empty or corrupted."""
        if not value or 'objects' not in value:
            raise serializers.ValidationError("Invalid design data. No objects found.")
        return value

    def validate_preview_image(self, value):
        """Standard file size and extension validation."""
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("Image file too large (Max 10MB).")
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.svg']
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError(f"Unsupported format {ext}. Use JPG, PNG, or SVG.")
        
        return value