from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken, UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        access = AccessToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'access': str(access)
        }, status=status.HTTP_201_CREATED)


class UserLoginView(generics.GenericAPIView):
    """View for user login."""

    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = authenticate(
            request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if user:
            access = AccessToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(access)
            })
        
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserLogoutView(APIView):
    """View for user logout (blacklist token if enabled)."""
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            # Extract token from header (assuming 'Authorization: Bearer <token>')
            token = request.auth  # Already authenticated, so token is available
            token.blacklist()  # Blacklist if SIMPLE_JWT blacklisting is enabled
            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)
        except (InvalidToken, TokenError):
            return Response({"detail": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Address
from .serializers import AddressSerializer

class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all addresses for the authenticated user."""
        addresses = Address.objects.filter(user=request.user)
        serializer = AddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new address."""
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(Address, pk=pk, user=user)

    def put(self, request, pk):
        """Update an existing address."""
        address = self.get_object(pk, request.user)
        serializer = AddressSerializer(address, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Delete an address."""
        address = self.get_object(pk, request.user)
        address.delete()
        return Response({"message": "Address deleted"}, status=status.HTTP_204_NO_CONTENT)

class SetDefaultAddressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """Set a specific address as the default."""
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.is_default = True
        address.save() # The model save method handles unsetting other defaults
        return Response({"message": f"Address {pk} is now the default"})




from rest_framework.permissions import AllowAny
from .models import EmailSubscriber
from .serializers import EmailSubscriberSerializer

class EmailSubscribeView(generics.CreateAPIView):
    queryset = EmailSubscriber.objects.all()
    serializer_class = EmailSubscriberSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # You could trigger a 'Welcome Email' here via a background task
        serializer.save()




from rest_framework.response import Response
from rest_framework import status
from lensra.core.tasks.sendgrid import send_welcome_email
from lensra.utils.coupons import generate_coupon_for_email

class EmailSubscribeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailSubscriberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        source = serializer.validated_data.get('source', 'popup')

        subscriber, created = EmailSubscriber.objects.get_or_create(
            email=email,
            defaults={"source": source}
        )

        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save()

        coupon_code = generate_coupon_for_email(email)

        send_welcome_email.delay(email, coupon_code)

        return Response(
            {"message": "Welcome to Lensra ✨ Check your email."},
            status=status.HTTP_201_CREATED
        )
