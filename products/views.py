from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, DesignPlacement, Category
from .serializers import (
    ProductSerializer, 
    ProductListSerializer, 
    DesignPlacementSerializer,
    CategorySerializer
)
import django_filters

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="base_price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="base_price", lookup_expr='lte')
    category = django_filters.CharFilter(field_name="categories__slug", lookup_expr='exact')

    class Meta:
        model = Product
        fields = ['is_customizable', 'is_featured', 'is_trending']

class CategoryListView(generics.ListAPIView):
    """Returns list of categories for navigation/filtering."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)\
        .prefetch_related('categories', 'variants__attributes__attribute', 'printable_areas')
    
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter 
    search_fields = ['name']
    ordering_fields = ['base_price']
    

class ProductDetailView(generics.RetrieveAPIView):
    """Detailed view for the editor: Loads product, print zones, and all variants."""
    queryset = Product.objects.filter(is_active=True)\
        .prefetch_related('categories', 'variants__attributes__attribute', 'printable_areas')
        
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

class ProductDetail(generics.RetrieveAPIView):
    """Detailed view for the editor: Loads product, print zones, and all variants."""
    queryset = Product.objects.filter(is_active=True)\
        .prefetch_related('categories', 'variants__attributes__attribute', 'printable_areas')
        
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'

class DesignPlacementCreateView(generics.CreateAPIView):
    """Saves a specific layout (JSON) onto a product area."""
    queryset = DesignPlacement.objects.all()
    serializer_class = DesignPlacementSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save()

class FeaturedProductsView(generics.ListAPIView):
    """Returns featured products with variant data for homepage highlights."""
    queryset = Product.objects.filter(is_active=True, is_featured=True)\
        .prefetch_related('categories', 'variants__attributes__attribute')
        
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]




from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from django.db.models import Count

class GiftRecommendationView(APIView):
    def get(self, request):
        # 1. Get parameters from Next.js request
        tags_raw = request.query_params.get('tags', '')
        max_price = request.query_params.get('price')
        
        tag_list = [tag.strip() for tag in tags_raw.split(',') if tag.strip()]
        
        # 2. Start with a base queryset
        queryset = Product.objects.all()

        # 3. Filter by Price (if provided)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)

        # 4. Filter by Tags and Rank by Relevance
        # We want products that match the MOST tags to appear first
        if tag_list:
            queryset = queryset.filter(tags__slug__in=tag_list).annotate(
                match_count=Count('tags')
            ).order_by('-match_count', '-id')

        # 5. Limit results to top 6 for a clean UI
        recommendations = queryset[:6]
        
        serializer = ProductSerializer(recommendations, many=True)
        return Response({
            "count": len(serializer.data),
            "results": serializer.data
        })