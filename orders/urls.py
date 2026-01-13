from django.urls import path
from . import views

urlpatterns = [
    # Cart endpoints
    path('cart/', views.CartItemListCreateView.as_view(), name='cart-list'),
    path('cart/<int:pk>/', views.CartItemDetailView.as_view(), name='cart-detail'),

    # Order endpoints
    path('orders/', views.OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
]