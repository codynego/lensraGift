from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
# Assuming these apps exist in your project
from products.models import Product, DesignPlacement 
from designs.models import Design

class CartItem(models.Model):
    # Nullable user to support guest sessions
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='cart_items'
    )
    # The key for guests
    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    
    placement = models.ForeignKey(DesignPlacement, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def total_price(self):
        # Always prioritize placement price if it exists
        if self.placement and self.placement.product:
            return self.placement.product.base_price * self.quantity
        if self.product:
            return self.product.base_price * self.quantity
        return 0

    def __str__(self):
        owner = self.user.email if self.user else f"Guest ({self.session_id[:8]})"
        item_name = self.placement.product.name if self.placement else (self.product.name if self.product else "Unknown")
        return f"{owner} - {item_name}"


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
    session_id = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    # Payment Information
    payment_reference = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
            owner = self.user.email if self.user else (self.guest_email or f"Guest {self.session_id[:8]}")
            return f"Order {self.order_number} ({owner})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    
    # Custom design
    placement = models.ForeignKey(
        DesignPlacement, 
        on_delete=models.PROTECT, 
        related_name='order_items',
        blank=True,
        null=True
    )
    # NEW: Plain product reference
    product = models.ForeignKey(
        'products.Product', # Adjust the app name string if necessary
        on_delete=models.PROTECT,
        blank=True,
        null=True
    )
    
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        name = self.placement.product.name if self.placement else self.product.name
        return f"{self.quantity}x {name} (Order: {self.order.order_number})"

    def save(self, *args, **kwargs):
        # Handle price lookup safely
        if not self.unit_price:
            if self.placement:
                self.unit_price = self.placement.product.base_price
            elif self.product:
                self.unit_price = self.product.base_price
                
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)