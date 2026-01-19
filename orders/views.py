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


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, F
from .models import CartItem

class CartSummaryView(APIView):
    """
    Returns a lightweight summary of the cart (count and total price)
    Works for both logged-in users and guests via session_id.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # 1. Identify the user/session
        session_id = request.headers.get('X-Session-ID')
        
        if request.user.is_authenticated:
            queryset = CartItem.objects.filter(user=request.user)
        else:
            queryset = CartItem.objects.filter(session_id=session_id) if session_id else CartItem.objects.none()

        # 2. Calculate Totals
        # We aggregate quantity and calculate price * quantity for each item
        totals = queryset.aggregate(
            total_qty=Sum('quantity'),
            total_amt=Sum(
                # Logic: If variant price exists use it, otherwise use product base price
                # We use Case/When for database-level calculation or simple F expressions
                F('quantity') * F('product__base_price')
            )
        )

        # 3. Formulate Response
        data = {
            "total_quantity": totals.get('total_qty') or 0,
            "total_price": totals.get('total_amt') or 0.00,
            "wishlist_count": 0  # You can add wishlist logic here later
        }

        return Response(data)

from .models import OrderItem


class GetSecretMessageView(APIView):
    """
    Retrieve the secret message and emotion for a given order item using its reveal token.
    """
    permission_classes = [AllowAny]

    def get(self, request, reveal_token):
        try:
            order_item = OrderItem.objects.get(reveal_token=reveal_token)
            data = {
                "secret_message": order_item.secret_message,
                "emotion": order_item.emotion
            }
            return Response(data, status=status.HTTP_200_OK)
        except OrderItem.DoesNotExist:
            return Response({"error": "Invalid token"}, status=status.HTTP_404_NOT_FOUND)






from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order  # Assuming models.py is in the same app
from .serializers import OrderSerializer  # Assuming serializers.py exists


class TrackOrderView(APIView):
    """
    Track an order using the order number and email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        order_number = request.data.get('order_number')
        email = request.data.get('email')

        if not order_number or not email:
            return Response({"error": "Both order_number and email are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(
                Q(guest_email=email) | Q(user__email=email),
                order_number=order_number
            )
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found with provided details."}, status=status.HTTP_404_NOT_FOUND)