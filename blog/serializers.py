from rest_framework import serializers
from .models import BlogPost

class BlogPostSerializer(serializers.ModelSerializer):
    featured_image_url = serializers.SerializerMethodField()
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'slug', 'featured_image', 
            'content', 'created_at', 'is_published', 'featured_image_url'
        ]

    def get_featured_image_url(self, obj):
        if obj.featured_image:
            url = obj.featured_image.url
            
            # Add Cloudinary transformations for optimization
            # This works if you're using CloudinaryField
            if hasattr(obj.featured_image, 'build_url'):
                url = obj.featured_image.build_url(
                    quality='auto',           # Automatic quality adjustment
                    fetch_format='auto',      # Automatic format (WebP for supported browsers)
                    width=800,                # Resize to appropriate width
                    crop='limit',             # Don't upscale, only downscale
                    flags='progressive'       # Progressive JPEG loading
                )
            
            if url.startswith('http://'):
                url = 'https://' + url[7:]
            return url
        return None