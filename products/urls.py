from django.urls import path
from .views import (
    ProductListView, 
    ProductDetailView, 
    DesignPlacementCreateView,
    CategoryListView,
    FeaturedProductsView
)

app_name = 'products'

urlpatterns = [
    # 1. Static/List Routes (Place these first)
    path('', ProductListView.as_view(), name='product-list'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('featured/', FeaturedProductsView.as_view(), name='featured-products'),
    
    # 2. Action Routes
    path('placements/create/', DesignPlacementCreateView.as_view(), name='design-placement-create'),

    # 3. Dynamic Routes (Place slugs/IDs last)
    # This captures everything else, so it must be at the bottom
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
]