from rest_framework import viewsets, permissions
from .models import BlogPost
from .serializers import BlogPostSerializer

class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = BlogPost.objects.filter(is_published=True).order_by('-created_at')
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'  # Allows fetching by /blog/my-post-title/ instead of ID
    permission_classes = [permissions.AllowAny]