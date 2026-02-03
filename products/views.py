from rest_framework import generics, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, DesignPlacement, Category, Tag
from .serializers import (
    ProductSerializer, 
    ProductListSerializer, 
    DesignPlacementSerializer,
    CategorySerializer,
    TagSerializer,
)
import django_filters





import django_filters
from .models import Product, Tag


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(
        field_name="base_price",
        lookup_expr='gte'
    )
    max_price = django_filters.NumberFilter(
        field_name="base_price",
        lookup_expr='lte'
    )

    category = django_filters.CharFilter(
        field_name="categories__slug",
        lookup_expr='exact'
    )

    tag = django_filters.ModelMultipleChoiceFilter(
        field_name="tags__slug",   # change to tags__id if you prefer
        to_field_name="slug",
        queryset=Tag.objects.all()
    )

    class Meta:
        model = Product
        fields = [
            'is_customizable',
            'is_featured',
            'is_trending',
            'category',
            'tag',
        ]


class CategoryListView(generics.ListAPIView):
    """Returns list of categories for navigation/filtering."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CategoryDetailView(generics.RetrieveAPIView):
    """Returns detailed info for a specific category."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

class TagListView(generics.ListAPIView):
    """Returns list of tags for filtering."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
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



from django.db.models import Q



class FeaturedProductsView(generics.ListAPIView):
    """
    Returns featured or trending non-customizable products.
    Supports filtering by tags, category, price, etc.
    """

    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = ProductFilter
    search_fields = ['name']
    ordering_fields = ['base_price']

    def get_queryset(self):
        return (
            Product.objects
            .filter(is_active=True)
            .filter(Q(is_featured=True) | Q(is_trending=True))
            .exclude(is_customizable=True)
            .prefetch_related(
                'categories',
                'tags',  # ✅ IMPORTANT: prefetch tags
                'variants__attributes__attribute'
            )
            .order_by('?')  # randomize for homepage freshness
        )


from django.shortcuts import get_object_or_404
from django.db.models import Count

class RelatedProductsView(generics.ListAPIView):
    """
    Returns products related to the current product
    based on shared tags (primary signal).
    """

    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        product = get_object_or_404(
            Product.objects.prefetch_related('tags', 'categories'),
            slug=self.kwargs['slug'],
            is_active=True
        )

        product_tags = product.tags.all()

        # 1️⃣ Primary: products sharing the most tags
        related = (
            Product.objects
            .filter(is_active=True)
            .exclude(id=product.id)
            .filter(tags__in=product_tags)
            .annotate(shared_tags=Count('tags'))
            .order_by('-shared_tags', '?')
            .prefetch_related(
                'categories',
                'tags',
                'variants__attributes__attribute'
            )
        )

        # 2️⃣ Fallback: same category if tags are weak
        if not related.exists():
            related = (
                Product.objects
                .filter(
                    is_active=True,
                    categories__in=product.categories.all()
                )
                .exclude(id=product.id)
                .distinct()
                .order_by('?')
            )

        return related[:8]  # perfect number for UI
