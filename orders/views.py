from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import CartItem, Order
from .serializers import (
    CartItemSerializer, 
    OrderSerializer, 
    OrderCreateSerializer,
    CouponSerializer,
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

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer

class OrderListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        # Anyone can create an order (Guests or Users)
        if self.request.method == 'POST':
            return [AllowAny()]
        # Only logged-in users can list their history
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Order.objects.filter(user=user).prefetch_related('items__product', 'items__variant')
        
        # Guest View: If a guest provides their session_id in the URL params
        session_id = self.request.query_params.get('session_id')
        if session_id:
            return Order.objects.filter(session_id=session_id).prefetch_related('items__product')
            
        return Order.objects.none()

    def create(self, request, *args, **kwargs):
        # We override create to return the OrderSerializer (detailed) 
        # instead of the OrderCreateSerializer (input-only)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Switch to the detail serializer for the response
        response_serializer = OrderSerializer(order, context={'request': request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [AllowAny] 
    lookup_field = 'order_number' # Default to looking up by LRG-XXXX

    def get_queryset(self):
        # Optimizing with prefetch to avoid hitting DB for every item in the order
        return Order.objects.all().prefetch_related('items__product', 'items__variant')
    
    def get_object(self):
        """
        Custom lookup logic to handle both ID and Order Number.
        Also adds a security check for guests.
        """
        lookup_value = self.kwargs.get(self.lookup_field) or self.kwargs.get('pk')
        
        # 1. Try fetching by Order Number (LRG-...)
        if str(lookup_value).startswith('LRG-'):
            order = get_object_or_404(Order, order_number=lookup_value)
        else:
            # 2. Try fetching by ID
            order = get_object_or_404(Order, pk=lookup_value)

        # SECURITY CHECK: 
        # If order belongs to a user, only that user can see it.
        # If guest order, anyone with the link can see it (Success Page logic).
        if order.user and order.user != self.request.user:
            self.permission_denied(self.request, message="You do not have access to this order.")
            
        return order


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


    

# views.py
from rest_framework import generics
from .models import ShippingZone, ShippingOption
from .serializers import ShippingZoneSerializer, ShippingOptionSerializer

class ShippingZoneListView(generics.ListAPIView):
    """
    Returns all shipping zones with their associated cities (locations).
    """
    queryset = ShippingZone.objects.all().prefetch_related('locations')
    serializer_class = ShippingZoneSerializer
    permission_classes = [AllowAny]

class ShippingOptionListView(generics.ListAPIView):
    """
    Returns speed options like 'Standard' or 'Express'.
    """
    queryset = ShippingOption.objects.filter(additional_cost__gte=0) # Only active options
    serializer_class = ShippingOptionSerializer
    permission_classes = [AllowAny]



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from decimal import Decimal
from .models import Coupon



class ValidateCouponView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        code = request.data.get('code')
        subtotal = request.data.get('subtotal')

        if not code:
            return Response({"error": "Please enter a coupon code."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Case-insensitive lookup
            coupon = Coupon.objects.get(code__iexact=code)
            
            # 1. Check basic validity (active, expired, usage limits)
            if not coupon.can_be_used():
                return Response({"error": "This coupon is no longer valid."}, status=status.HTTP_400_BAD_REQUEST)

            # 2. Check minimum order amount
            if subtotal:
                subtotal_dec = Decimal(str(subtotal))
                if coupon.min_order_amount and subtotal_dec < coupon.min_order_amount:
                    return Response({
                        "error": f"Minimum order of ₦{coupon.min_order_amount:,.2f} required for this code."
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                subtotal_dec = Decimal('0.00')

            # 3. Calculate the discount preview
            if coupon.discount_type == Coupon.PERCENTAGE:
                discount_amount = (coupon.value / 100) * subtotal_dec
            else:
                discount_amount = coupon.value

            return Response({
                "valid": True,
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "value": coupon.value,
                "discount_amount": float(min(discount_amount, subtotal_dec))
            }, status=status.HTTP_200_OK)

        except Coupon.DoesNotExist:
            return Response({"error": "Invalid coupon code."}, status=status.HTTP_404_NOT_FOUND)