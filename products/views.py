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
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db.models import Count, Q
from .models import Product
from .serializers import ProductSerializer

class GiftRecommendationsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # 1. Extract tag slugs from the URL query params
        raw_tags = request.query_params.get('tags', '')
        if not raw_tags:
            return Response({"results": []})
            
        tag_slugs = [t.strip() for t in raw_tags.split(',') if t.strip()]
        
        # 2. Separate price tags from descriptive tags for cleaner logic
        price_tags = [t for t in tag_slugs if t.startswith('budget-')]
        interest_tags = [t for t in tag_slugs if not t.startswith('budget-')]
        
        # 3. Base Query: Only active products
        products = Product.objects.filter(is_active=True)

        # 4. Apply Hard Budget Filters (if applicable)
        if 'budget-low' in price_tags:
            products = products.filter(base_price__lt=15000)
        elif 'budget-mid' in price_tags:
            products = products.filter(base_price__range=(15000, 50000))
        elif 'budget-high' in price_tags:
            products = products.filter(base_price__gt=50000)

        # 5. THE RANKING ENGINE: 
        # - Filter for products containing at least one of the interest tags
        # - Count how many of those tags match (relevance score)
        # - Order by the count (descending) then by featured status
        products = products.filter(tags__slug__in=interest_tags) \
            .annotate(relevance_score=Count('tags', filter=Q(tags__slug__in=interest_tags))) \
            .order_by('-relevance_score', '-is_featured', 'base_price') \
            .distinct()

        # 6. Final limit and serialize
        results = products[:10]
        serializer = ProductSerializer(results, many=True)
        
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)