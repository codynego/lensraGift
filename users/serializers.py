from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


from rest_framework import serializers
from django.contrib.auth import get_user_model
from designs.models import Design
from orders.models import Order
from wishlists.models import WishlistItem

User = get_user_model()


from .models import Address
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'address_type', 'is_default', 'full_name', 
            'phone_number', 'street_address', 'apartment_suite', 
            'city', 'state', 'postal_code', 'country', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        # Ensure fields that can be empty are handled
        extra_kwargs = {
            'apartment_suite': {'required': False, 'allow_blank': True},
            'postal_code': {'required': False, 'allow_blank': True},
        }

    def validate(self, data):
        # Log the data to your terminal to see what's arriving
        print("Incoming Address Data:", data)
        return data

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the User model including dashboard stats."""
    addresses = AddressSerializer(many=True, read_only=True)
    design_count = serializers.SerializerMethodField()
    active_orders_count = serializers.SerializerMethodField()
    wishlist_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number', 
            'date_joined', 'design_count', 'active_orders_count', 
            'wishlist_count', 'reward_points', 'addresses'
        ]
        read_only_fields = ['id', 'date_joined', 'design_count', 'active_orders_count', 'wishlist_count', 'reward_points', 'addresses']

    def get_design_count(self, obj):
        return Design.objects.filter(user=obj).count()

    def get_active_orders_count(self, obj):
        return Order.objects.filter(user=obj, status='active').count()

    def get_wishlist_count(self, obj):
        return WishlistItem.objects.filter(wishlist__user=obj).count()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'phone_number']

    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """Create a new user with encrypted password."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})



from .models import EmailSubscriber

class EmailSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSubscriber
        fields = ['id', 'email', 'source', 'subscribed_at', 'is_active']
        read_only_fields = ['id', 'subscribed_at', 'is_active']

    def validate_email(self, value):
        email = value.lower()

        existing = EmailSubscriber.objects.filter(email=email).first()

        if existing and existing.is_active:
            raise serializers.ValidationError(
                "You’re already on the Lensra list 😄"
            )

        return email
