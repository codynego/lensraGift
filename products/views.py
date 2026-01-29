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



from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Product
from .serializers import ProductSerializer

class GiftRecommendationsView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request): # Changed to POST to match your latest frontend request
        tag_slugs = request.data.get('tags', [])
        
        # 1. Start with active products
        query = Q(is_active=True)
        
        # 2. Add budget logic (Optional: removing 'budget-mid' from tags to avoid filtering issues)
        price_tags = [t for t in tag_slugs if t.startswith('budget-')]
        other_tags = [t for t in tag_slugs if not t.startswith('budget-')]
        
        products = Product.objects.filter(query)

        if 'budget-low' in price_tags:
            products = products.filter(base_price__lt=15000)
        elif 'budget-mid' in price_tags:
            products = products.filter(base_price__range=(15000, 50000))
        elif 'budget-high' in price_tags:
            products = products.filter(base_price__gt=50000)

        # 3. THE RELEVANCE ENGINE:
        # We filter for products that have at least one matching tag,
        # then we count how many of the requested tags each product has.
        products = products.filter(tags__slug__in=other_tags) \
            .annotate(num_matches=Count('tags', filter=Q(tags__slug__in=other_tags))) \
            .order_by('-num_matches', '-is_featured', 'base_price') \
            .distinct()

        # 4. Limit to top 10
        results = products[:10]

        serializer = ProductSerializer(results, many=True)
        return Response({"results": serializer.data})