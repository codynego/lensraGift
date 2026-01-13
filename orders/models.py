from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
# Assuming these apps exist in your project
from products.models import Product, DesignPlacement 
from designs.models import Design

class CartItem(models.Model):
    """Temporary items stored before checkout."""
    # Fixed: Use settings.AUTH_USER_MODEL for consistency
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='cart_items'
    )
    # Fixed: Ensure DesignPlacement is imported or referenced as string
    placement = models.ForeignKey(
        DesignPlacement, 
        on_delete=models.CASCADE,
        related_name='cart_entries'
    )
    quantity = models.PositiveIntegerField(
        default=1, 
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_price(self):
        # Calculates price based on the product associated with the placement
        return self.placement.product.base_price * self.quantity

    def __str__(self):
        return f"{self.user.email}'s cart: {self.placement.product.name}"


from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator

class Order(models.Model):
    """Finalized customer orders supporting both registered users and guests."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    # Change: allow null for guest checkout
    # Change: SET_NULL preserves order history if user is deleted
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        related_name='orders',
        null=True,
        blank=True
    )
    
    # New: Identify guest buyers
    guest_email = models.EmailField(max_length=255, blank=True, null=True)
    
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)]
    )
    
    # Shipping Information
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_country = models.CharField(max_length=100, default='Nigeria')
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    phone_number = models.CharField(max_length=20)
    
    # Payment Information
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        owner = self.user.email if self.user else self.guest_email
        return f"Order {self.order_number} ({owner})"


class OrderItem(models.Model):
    """Items snapshot at the moment of purchase."""
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    # Fixed: Pointing to placement preserves the design data/mockup for production
    placement = models.ForeignKey(
        DesignPlacement, 
        on_delete=models.PROTECT, 
        related_name='order_items',
        blank=True,
        null=True
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # We store these as hard values in case the product price changes in the future
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.placement.product.name} (Order: {self.order.order_number})"

    def save(self, *args, **kwargs):
        """Auto-calculate subtotal and pull current price if not set."""
        if not self.unit_price:
            self.unit_price = self.placement.product.base_price
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)