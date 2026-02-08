from django.urls import path
from .views import (
    ProductListView, 
    ProductDetailView, 
    DesignPlacementCreateView,
    CategoryListView,
    FeaturedProductsView,
    ProductDetail,
    GiftRecommendationsView,
    TagListView,
    CategoryDetailView,
    RelatedProductsView,
    SaleProductListView
)

app_name = 'products'

urlpatterns = [
    # 1. Static/List Routes (Place these first)
    path('', ProductListView.as_view(), name='product-list'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('deals/', SaleProductListView.as_view(), name='sale-products'),
    path('related/<slug:slug>/', RelatedProductsView.as_view(), name='related-products'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    path('featured/', FeaturedProductsView.as_view(), name='featured-products'),
    path('gift-finder/recommendations/', GiftRecommendationsView.as_view(), name='gift-recommendations'),
    
    # 2. Action Routes
    path('placements/create/', DesignPlacementCreateView.as_view(), name='design-placement-create'),

    # 3. Dynamic Routes (Place slugs/IDs last)
    # This captures everything else, so it must be at the bottom
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('id/<int:id>/', ProductDetail.as_view(), name='product-detail-by-id'),
    
]