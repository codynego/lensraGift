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

class GiftRecommendationsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 1. Get slugs from the frontend
        tag_slugs = request.query_params.get('tags', '').split(',')
        print(f"Received tag slugs for gift recommendations: {tag_slugs}")
        
        # 2. Filter products that match the slugs
        # Use .distinct() to avoid showing the same product twice if it matches 2 tags
        products = Product.objects.filter(
            tags__slug__in=tag_slugs, 
            is_active=True 
        ).distinct()
        print(f"Found {products.count()} products matching tags: {tag_slugs}")

        # 3. Handle Budget (Optional but highly recommended)
        # If one of your tags is 'budget-mid', you can define that range here
        if 'budget-mid' in tag_slugs:
            products = products.filter(base_price__range=(15000, 50000))
            print(f"Filtered products by budget-mid range: {products.count()}")

        # 4. Limit to 10 best matches
        products = products[:10]

        serializer = ProductSerializer(products, many=True)
        return Response({"results": serializer.data})