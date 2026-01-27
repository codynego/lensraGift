from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BlogPost
from .serializers import BlogPostSerializer


class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing blog posts.
    Provides list and detail views.
    """
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'
    
    def get_queryset(self):
        """
        Return only published posts, ordered by creation date (newest first)
        """
        return BlogPost.objects.filter(is_published=True).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """
        List all published blog posts
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        # Return a simple array (not paginated)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single blog post by slug
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except BlogPost.DoesNotExist:
            return Response(
                {"detail": "Post not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )