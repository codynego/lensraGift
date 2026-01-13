from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CartItem, Order
from .serializers import (
    CartItemSerializer, 
    OrderSerializer, 
    OrderCreateSerializer
)

# --- CART VIEWS ---

class CartItemListCreateView(generics.ListCreateAPIView):
    """View to see items in cart and add new design placements to cart."""
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Ensure the cart item is linked to the logged-in user
        serializer.save(user=self.request.user)

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View to update quantity or remove an item from the cart."""
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user)


# --- ORDER VIEWS ---
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer

class OrderListCreateView(generics.ListCreateAPIView):
    """
    GET: View order history (Logged in only).
    POST: Checkout (Anyone - converts cart or JSON items to order).
    """
    # Change: POST must be allowed for everyone to support Guest Checkout
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        # Guests can't list orders, only authenticated users see their own
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user).prefetch_related('items')
        return Order.objects.none()

    def perform_create(self, serializer):
        # We handle 'user' inside the Serializer's create method now,
        # so we just call save() here.
        serializer.save()

class OrderDetailView(generics.RetrieveAPIView):
    """View specific order details. Guests can view via order_number (optional logic)."""
    serializer_class = OrderSerializer
    # If you want guests to see their success page, change this to AllowAny 
    # and filter by order_number instead of user
    permission_classes = [AllowAny] 

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user)
        # If guest, allow lookup by ID (usually you'd use a UUID or session check here)
        return Order.objects.all()