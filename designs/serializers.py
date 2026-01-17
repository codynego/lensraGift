from rest_framework import serializers
from .models import Design, DesignImage
import os

class DesignImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DesignImage
        fields = ['id', 'image', 'image_url', 'placement_note']

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None


class DesignSerializer(serializers.ModelSerializer):
    preview_image_url = serializers.SerializerMethodField()
    images = DesignImageSerializer(many=True, read_only=True)

    class Meta:
        model = Design
        fields = [
            'id', 'user', 'user_email', 'name', 'custom_text', 
            'overall_instructions', 'preview_image', 'preview_image_url', 'images', 
            'created_at', 'updated_at'
        ]

    def get_preview_image_url(self, obj):
        if obj.preview_image:
            return obj.preview_image.url
        return None

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
        request = self.context.get('request')
        images_data = []

        index = 0
        while f'image_{index}' in request.FILES:
            images_data.append({
                'image': request.FILES.get(f'image_{index}'),
                'placement_note': request.data.get(f'note_{index}', '')
            })
            index += 1

        design = Design.objects.create(**validated_data)

        # Create DesignImages
        for item in images_data:
            DesignImage.objects.create(design=design, **item)

        # Auto-generate preview if missing
        if not design.preview_image and images_data:
            first_img = images_data[0]['image']
            design.preview_image = first_img
            design.save()

        return design
