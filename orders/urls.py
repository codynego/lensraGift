from django.urls import path
from . import views
from .views import CartSummaryView

urlpatterns = [
    # Cart endpoints
    path('cart/', views.CartItemListCreateView.as_view(), name='cart-list'),
    path('cart/<int:pk>/', views.CartItemDetailView.as_view(), name='cart-detail'),

    # Order endpoints
    path('orders/', views.OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),

    path('cart/summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('secret-message/<uuid:reveal_token>/', views.GetSecretMessageView.as_view(), name='secret-message-reveal'),
    path('track-order/', views.TrackOrderView.as_view(), name='track-order'),
]