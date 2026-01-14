from django.urls import path
from .views import (
    ProductListView, 
    ProductDetailView, 
    DesignPlacementCreateView,
    CategoryListView,
    FeaturedProductsView
     # Renamed for consistency with your View
)

app_name = 'products'

urlpatterns = [
    # GET: List all products (supports ?category= & ?search=)
    path('', ProductListView.as_view(), name='product-list'),
    
    # GET: Retrieve specific product and its printable areas by slug
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    
    # POST: Save a new design layout/mockup
    path('placements/create/', DesignPlacementCreateView.as_view(), name='design-placement-create'),

    # GET: List all product categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    # GET: List featured products
    path('featured/', FeaturedProductsView.as_view(), name='featured-products'),
]
