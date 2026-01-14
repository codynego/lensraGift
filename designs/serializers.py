from rest_framework import serializers
from .models import Design, DesignImage
import os

class DesignImageSerializer(serializers.ModelSerializer):
    """Handles individual asset uploads within a design."""
    class Meta:
        model = DesignImage
        fields = ['id', 'image', 'placement_note']

class DesignSerializer(serializers.ModelSerializer):
    """Full detail serializer including nested images."""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    images = DesignImageSerializer(many=True, read_only=True)

    class Meta:
        model = Design
        fields = [
            'id', 'user', 'user_email', 'name', 'custom_text', 
            'overall_instructions', 'preview_image', 'images', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

class DesignCreateSerializer(serializers.ModelSerializer):
    """
    Handles Multipart FormData from the Editor page.
    Creates both the Design and associated DesignImages.
    """
    class Meta:
        model = Design
        fields = ['name', 'custom_text', 'overall_instructions', 'preview_image', 'session_id']

    def validate_preview_image(self, value):
        """Standard file size and extension validation."""
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("Image file too large (Max 10MB).")
        
        valid_extensions = ['.jpg', '.jpeg', '.png', '.svg', '.webp']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in valid_extensions:
            raise serializers.ValidationError(f"Unsupported format {ext}. Use JPG, PNG, or SVG.")
        return value

    def create(self, validated_data):
        # 1. Grab files from the raw request (passed via context)
        request = self.context.get('request')
        images_data = []
        
        # We loop through request.FILES to find keys like 'image_0', 'image_1'
        index = 0
        while f'image_{index}' in request.FILES:
            images_data.append({
                'image': request.FILES.get(f'image_{index}'),
                'placement_note': request.data.get(f'note_{index}', '')
            })
            index += 1

        # 2. Create the main Design
        design = Design.objects.create(**validated_data)

        # 3. Create the nested DesignImage objects
        for item in images_data:
            DesignImage.objects.create(design=design, **item)

        return design