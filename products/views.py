from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, DesignPlacement, Category
from .serializers import (
    ProductSerializer, 
    ProductListSerializer, 
    DesignPlacementSerializer,
    CategorySerializer
)

class CategoryListView(generics.ListAPIView):
    """Returns list of categories for navigation/filtering."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ProductListView(generics.ListAPIView):
    """Main shop view: Filters and searches active products."""
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    filterset_fields = ['category', 'is_customizable', 'is_featured', 'is_trending']
    search_fields = ['name', 'description']
    ordering_fields = ['base_price', 'created_at']

class ProductDetailView(generics.RetrieveAPIView):
    """Detailed view for the editor: Loads the product + its print zones."""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

class DesignPlacementCreateView(generics.CreateAPIView):
    """
    Saves a specific layout (JSON) onto a product area.
    This is called when a user finishes designing.
    """
    queryset = DesignPlacement.objects.all()
    serializer_class = DesignPlacementSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Additional logic can be added here, like linking to a user session
        serializer.save()



