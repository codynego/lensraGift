from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import BlogPost, BlogCategory
from .serializers import BlogPostSerializer, BlogCategorySerializer

class BlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing Lensra blog posts.
    Supports filtering by category and fetching categories.
    """
    serializer_class = BlogPostSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """
        Filters posts by published status and optionally by category slug.
        """
        queryset = BlogPost.objects.filter(is_published=True).order_by('-created_at')
        
        # Enable filtering by category slug: /api/blog/posts/?category=gifting-tips
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
            
        return queryset
    
    def list(self, request, *args, **kwargs):
        """
        List all published blog posts (supports category filtering).
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single blog post by slug.
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except BlogPost.DoesNotExist:
            return Response(
                {"detail": "Story not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """
        Endpoint to get all categories for the frontend filter menu.
        Access via: /api/blog/posts/categories/
        """
        categories = BlogCategory.objects.all()
        serializer = BlogCategorySerializer(categories, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Returns the latest 3 posts for the homepage.
        Access via: /api/blog/posts/featured/
        """
        queryset = self.get_queryset()[:3]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)