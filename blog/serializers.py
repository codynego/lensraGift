from rest_framework import serializers
from .models import BlogPost, BlogCategory

class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ['id', 'name', 'slug']

class BlogPostSerializer(serializers.ModelSerializer):
    featured_image_url = serializers.SerializerMethodField()
    # This provides full category info (name and slug) instead of just an ID
    category_details = BlogCategorySerializer(source='category', read_only=True)
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'category', 'category_details', 'title', 'slug', 
            'featured_image', 'featured_image_url', 'content', 
            'meta_title', 'meta_description', 'keywords', 'canonical_url',
            'created_at', 'is_published'
        ]

    def get_featured_image_url(self, obj):
        if obj.featured_image:
            # Check if it's a CloudinaryResource (CloudinaryField)
            if hasattr(obj.featured_image, 'build_url'):
                url = obj.featured_image.build_url(
                    quality='auto',
                    fetch_format='auto',
                    width=1200, # Increased for high-res blog headers
                    crop='limit',
                    flags='progressive'
                )
            else:
                url = obj.featured_image.url
            
            # Secure URL enforcement
            if url.startswith('http://'):
                url = 'https://' + url[7:]
            return url
        return None