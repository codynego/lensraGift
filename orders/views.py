from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import CartItem, Order
from .serializers import (
    CartItemSerializer, 
    OrderSerializer, 
    OrderCreateSerializer
)

# --- CART VIEWS ---

class CartItemListCreateView(generics.ListCreateAPIView):
    """Handles both Authenticated and Guest (session-based) carts."""
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny] # Must be AllowAny to support guests

    def get_queryset(self):
        user = self.request.user
        session_id = self.request.query_params.get('session_id')

        if user.is_authenticated:
            # Show items belonging to user
            return CartItem.objects.filter(user=user)
        elif session_id:
            # Show items belonging to session
            return CartItem.objects.filter(session_id=session_id, user__isnull=True)
        return CartItem.objects.none()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        session_id = self.request.data.get('session_id')
        
        # Link to user if logged in, otherwise link to session_id
        serializer.save(
            user=user,
            session_id=None if user else session_id
        )

class CartItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Update or delete items using either user ownership or session_id."""
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user = self.request.user
        # We allow a broad queryset but the logic ensures you only touch what is yours
        if user.is_authenticated:
            return CartItem.objects.filter(user=user)
        
        # For guests, we filter by the session_id passed in the request
        session_id = self.request.query_params.get('session_id')
        return CartItem.objects.filter(session_id=session_id, user__isnull=True)

class MergeCartView(APIView):
    """
    Call this after Login/Signup to move guest items to the user's account.
    POST data: {"session_id": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({"error": "session_id required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Find all guest items for this session
        guest_items = CartItem.objects.filter(session_id=session_id, user__isnull=True)
        
        # Move them to the authenticated user
        count = guest_items.count()
        guest_items.update(user=request.user, session_id=None)
        
        return Response({"message": f"Merged {count} items to your account."}, status=status.HTTP_200_OK)


# --- ORDER VIEWS ---

class OrderListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Order.objects.filter(user=self.request.user).prefetch_related('items')
        
        # Optional: Allow guests to see their specific order if they have the session_id
        session_id = self.request.query_params.get('session_id')
        if session_id:
            return Order.objects.filter(session_id=session_id).prefetch_related('items')
            
        return Order.objects.none()

    def perform_create(self, serializer):
        serializer.save()

class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        # We allow lookup by order_number for the success page
        return Order.objects.all()
    
    def get_object(self):
        # Allow looking up by order_number instead of just ID
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        
        # If it's a numeric ID, use id, otherwise use order_number
        if str(self.kwargs[lookup_url_kwarg]).startswith('LRG-'):
            return generics.get_object_or_404(Order, order_number=self.kwargs[lookup_url_kwarg])
        return super().get_object()