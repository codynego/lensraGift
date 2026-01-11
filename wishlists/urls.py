from django.urls import path
from .views import WishlistDetailView, WishlistItemDeleteView

urlpatterns = [
    # GET to view, POST to add
    path('', WishlistDetailView.as_view(), name='wishlist-detail'),
    path('remove/<int:product_id>/', WishlistItemDeleteView.as_view(), name='wishlist-remove'),
]